"""
Claude API Budget Manager for ARA v2.
Manages Claude API budget and rate limiting to prevent cost overruns.
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from ara_v2.utils.redis_client import get_redis
from ara_v2.utils.errors import BudgetExceededError

logger = logging.getLogger(__name__)


class ClaudeAPIBudgetManager:
    """Manages Claude API budget and rate limiting."""

    def __init__(self, redis_client=None, config=None):
        """
        Initialize budget manager.

        Args:
            redis_client: Redis client instance (uses global if not provided)
            config: Flask app config (uses defaults if not provided)
        """
        self.redis = redis_client or get_redis()
        self.logger = logger

        # Budget configuration (from config or defaults)
        if config:
            self.DAILY_BUDGET_USD = config.get('CLAUDE_DAILY_BUDGET', 5.00)
            self.MONTHLY_BUDGET_USD = config.get('CLAUDE_MONTHLY_BUDGET', 100.00)
            self.MAX_CALLS_PER_MINUTE = config.get('CLAUDE_MAX_CALLS_PER_MIN', 10)
            self.MAX_CALLS_PER_HOUR = config.get('CLAUDE_MAX_CALLS_PER_HOUR', 200)
        else:
            self.DAILY_BUDGET_USD = 5.00
            self.MONTHLY_BUDGET_USD = 100.00
            self.MAX_CALLS_PER_MINUTE = 10
            self.MAX_CALLS_PER_HOUR = 200

        # Cost per call estimate (updated with actual costs)
        self.ESTIMATED_COST_PER_CALL = 0.007  # $0.007 per evaluation

    def check_budget(self) -> dict:
        """
        Check if budget allows for more API calls.

        Returns:
            dict: Budget status with daily/monthly spent and remaining
        """
        if not self.redis:
            # If Redis is unavailable, allow calls but log warning
            self.logger.warning("Redis unavailable, budget checks disabled")
            return {
                'can_proceed': True,
                'daily_spent': 0,
                'daily_remaining': self.DAILY_BUDGET_USD,
                'monthly_spent': 0,
                'monthly_remaining': self.MONTHLY_BUDGET_USD,
                'estimated_calls_remaining_today': 999999,
                'estimated_calls_remaining_month': 999999
            }

        today = datetime.utcnow().date().isoformat()
        month = datetime.utcnow().strftime('%Y-%m')

        daily_spent = float(self.redis.get(f'claude:budget:daily:{today}') or 0)
        monthly_spent = float(self.redis.get(f'claude:budget:monthly:{month}') or 0)

        daily_remaining = self.DAILY_BUDGET_USD - daily_spent
        monthly_remaining = self.MONTHLY_BUDGET_USD - monthly_spent

        return {
            'can_proceed': (
                daily_remaining >= self.ESTIMATED_COST_PER_CALL and
                monthly_remaining >= self.ESTIMATED_COST_PER_CALL
            ),
            'daily_spent': daily_spent,
            'daily_remaining': daily_remaining,
            'monthly_spent': monthly_spent,
            'monthly_remaining': monthly_remaining,
            'estimated_calls_remaining_today': int(daily_remaining / self.ESTIMATED_COST_PER_CALL),
            'estimated_calls_remaining_month': int(monthly_remaining / self.ESTIMATED_COST_PER_CALL)
        }

    def check_rate_limit(self) -> dict:
        """
        Check if rate limits allow for more API calls.

        Returns:
            dict: Rate limit status
        """
        if not self.redis:
            return {
                'can_proceed': True,
                'calls_this_minute': 0,
                'calls_this_hour': 0,
                'limit_per_minute': self.MAX_CALLS_PER_MINUTE,
                'limit_per_hour': self.MAX_CALLS_PER_HOUR
            }

        now = datetime.utcnow()
        minute_key = f"claude:ratelimit:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
        hour_key = f"claude:ratelimit:hour:{now.strftime('%Y-%m-%d-%H')}"

        calls_this_minute = int(self.redis.get(minute_key) or 0)
        calls_this_hour = int(self.redis.get(hour_key) or 0)

        return {
            'can_proceed': (
                calls_this_minute < self.MAX_CALLS_PER_MINUTE and
                calls_this_hour < self.MAX_CALLS_PER_HOUR
            ),
            'calls_this_minute': calls_this_minute,
            'calls_this_hour': calls_this_hour,
            'limit_per_minute': self.MAX_CALLS_PER_MINUTE,
            'limit_per_hour': self.MAX_CALLS_PER_HOUR
        }

    def record_call(self, actual_cost: float = None):
        """
        Record an API call and update budget/rate counters.

        Args:
            actual_cost: Actual cost of the API call (uses estimate if not provided)
        """
        if not self.redis:
            return

        cost = actual_cost or self.ESTIMATED_COST_PER_CALL
        now = datetime.utcnow()

        # Update budget counters
        today = now.date().isoformat()
        month = now.strftime('%Y-%m')

        self.redis.incrbyfloat(f'claude:budget:daily:{today}', cost)
        self.redis.expire(f'claude:budget:daily:{today}', 86400 * 2)  # 2 days

        self.redis.incrbyfloat(f'claude:budget:monthly:{month}', cost)
        self.redis.expire(f'claude:budget:monthly:{month}', 86400 * 60)  # 60 days

        # Update rate limit counters
        minute_key = f"claude:ratelimit:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
        hour_key = f"claude:ratelimit:hour:{now.strftime('%Y-%m-%d-%H')}"

        self.redis.incr(minute_key)
        self.redis.expire(minute_key, 120)  # 2 minutes

        self.redis.incr(hour_key)
        self.redis.expire(hour_key, 7200)  # 2 hours

        self.logger.info(f"Claude API call recorded: ${cost:.4f}")

    def can_make_call(self) -> tuple[bool, str]:
        """
        Check if API call is allowed under budget and rate limits.

        Returns:
            tuple: (can_proceed, reason)
        """
        budget_status = self.check_budget()
        if not budget_status['can_proceed']:
            if budget_status['daily_remaining'] < self.ESTIMATED_COST_PER_CALL:
                return False, "Daily budget exhausted"
            else:
                return False, "Monthly budget exhausted"

        rate_status = self.check_rate_limit()
        if not rate_status['can_proceed']:
            if rate_status['calls_this_minute'] >= self.MAX_CALLS_PER_MINUTE:
                return False, "Rate limit: too many calls per minute"
            else:
                return False, "Rate limit: too many calls per hour"

        return True, "OK"

    def add_to_pending_queue(self, paper_id: int):
        """
        Add paper to pending evaluation queue.

        Args:
            paper_id: ID of paper to queue
        """
        if not self.redis:
            return

        self.redis.zadd(
            'claude:pending_evaluations',
            {str(paper_id): datetime.utcnow().timestamp()}
        )
        self.logger.info(f"Paper {paper_id} added to pending evaluation queue")

    def get_pending_queue_size(self) -> int:
        """Get number of papers in pending evaluation queue."""
        if not self.redis:
            return 0
        return self.redis.zcard('claude:pending_evaluations')

    def get_pending_papers(self, limit: int = 10) -> list[int]:
        """
        Get papers from pending evaluation queue (oldest first).

        Args:
            limit: Maximum number of papers to return

        Returns:
            list: Paper IDs
        """
        if not self.redis:
            return []

        pending = self.redis.zrange('claude:pending_evaluations', 0, limit - 1)
        return [int(paper_id) for paper_id in pending]

    def remove_from_pending_queue(self, paper_id: int):
        """Remove paper from pending evaluation queue."""
        if not self.redis:
            return

        self.redis.zrem('claude:pending_evaluations', str(paper_id))
        self.logger.info(f"Paper {paper_id} removed from pending evaluation queue")


def with_budget_control(budget_manager: ClaudeAPIBudgetManager):
    """
    Decorator to enforce budget controls on Claude API calls.

    Args:
        budget_manager: ClaudeAPIBudgetManager instance

    Example:
        @with_budget_control(budget_manager)
        def evaluate_novelty(paper_id):
            # Make Claude API call
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if call is allowed
            can_proceed, reason = budget_manager.can_make_call()

            if not can_proceed:
                logger.warning(f"Claude API call blocked: {reason}")
                raise BudgetExceededError(reason)

            # Make the call
            result = func(*args, **kwargs)

            # Record the call (use actual cost if available in result)
            actual_cost = None
            if isinstance(result, dict) and 'cost' in result:
                actual_cost = result['cost']

            budget_manager.record_call(actual_cost)

            return result

        return wrapper
    return decorator


# Global budget manager instance (initialized in app factory)
_budget_manager = None


def init_budget_manager(app):
    """Initialize global budget manager with Flask app config."""
    global _budget_manager
    _budget_manager = ClaudeAPIBudgetManager(
        redis_client=get_redis(),
        config=app.config
    )
    app.logger.info("Claude API budget manager initialized")
    return _budget_manager


def get_budget_manager() -> ClaudeAPIBudgetManager:
    """Get global budget manager instance."""
    return _budget_manager
