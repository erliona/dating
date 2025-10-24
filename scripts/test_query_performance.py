#!/usr/bin/env python3
"""
Database query performance testing script.

Tests critical queries with EXPLAIN ANALYZE to ensure indexes are working.
"""
import asyncio
import os
import sys
import time
from typing import Dict, List, Tuple
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


class QueryPerformanceTester:
    """Test database query performance."""
    
    def __init__(self, database_url: str):
        """Initialize with database URL."""
        self.database_url = database_url
        self.engine = None
        self.results = []
    
    async def connect(self):
        """Connect to database."""
        self.engine = create_async_engine(self.database_url)
    
    async def disconnect(self):
        """Disconnect from database."""
        if self.engine:
            await self.engine.dispose()
    
    async def test_query(self, name: str, query: str, params: Dict = None) -> Dict:
        """Test a single query and return performance metrics."""
        start_time = time.time()
        
        try:
            async with self.engine.begin() as conn:
                # Use EXPLAIN ANALYZE to get detailed performance info
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = await conn.execute(text(explain_query), params or {})
                explain_result = result.fetchone()[0]
                
                execution_time = time.time() - start_time
                
                # Extract key metrics
                plan = explain_result[0]["Plan"]
                total_cost = plan.get("Total Cost", 0)
                actual_time = plan.get("Actual Total Time", 0)
                rows_returned = plan.get("Actual Rows", 0)
                
                return {
                    "name": name,
                    "query": query,
                    "execution_time": execution_time,
                    "total_cost": total_cost,
                    "actual_time": actual_time,
                    "rows_returned": rows_returned,
                    "plan": explain_result[0]
                }
                
        except Exception as e:
            return {
                "name": name,
                "query": query,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    async def run_performance_tests(self):
        """Run all performance tests."""
        print("🚀 Starting Database Performance Tests...")
        print("=" * 60)
        
        # Critical queries for dating app
        test_queries = [
            # Discovery queries
            {
                "name": "Discovery Candidates (Location-based)",
                "query": """
                    SELECT p.*, u.tg_username, u.last_active_at
                    FROM profiles p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.location && ST_MakeEnvelope($1, $2, $3, $4, 4326)
                    AND p.age BETWEEN $5 AND $6
                    AND p.gender = $7
                    AND p.user_id != $8
                    AND p.user_id NOT IN (
                        SELECT target_user_id FROM interactions 
                        WHERE user_id = $8
                    )
                    ORDER BY ST_Distance(p.location, ST_Point($9, $10, 4326))
                    LIMIT 20
                """,
                "params": {
                    "1": -74.0, "2": 40.7, "3": -73.9, "4": 40.8,  # NYC bounds
                    "5": 25, "6": 35, "7": "female", "8": 1,
                    "9": -73.935242, "10": 40.730610  # NYC center
                }
            },
            
            # Chat queries
            {
                "name": "Chat Messages (Pagination)",
                "query": """
                    SELECT m.*, u.tg_username as sender_username
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    WHERE m.conversation_id = $1
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 50
                """,
                "params": {"1": 1}
            },
            
            # Profile queries
            {
                "name": "User Profile with Photos",
                "query": """
                    SELECT p.*, u.tg_username, u.last_active_at,
                           array_agg(ph.url ORDER BY ph.sort_order) as photo_urls
                    FROM profiles p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN photos ph ON p.user_id = ph.user_id
                    WHERE p.user_id = $1
                    GROUP BY p.id, u.id
                """,
                "params": {"1": 1}
            },
            
            # Likes queries
            {
                "name": "Who Liked Me",
                "query": """
                    SELECT l.*, p.name, p.age, p.city, ph.url as photo_url
                    FROM likes l
                    JOIN profiles p ON l.liker_id = p.user_id
                    LEFT JOIN photos ph ON l.liker_id = ph.user_id AND ph.is_primary = true
                    WHERE l.liked_id = $1
                    ORDER BY l.created_at DESC
                    LIMIT 20
                """,
                "params": {"1": 1}
            },
            
            # Interactions queries
            {
                "name": "User Interactions (Recent)",
                "query": """
                    SELECT i.*, p.name, p.age, p.city
                    FROM interactions i
                    JOIN profiles p ON i.target_user_id = p.user_id
                    WHERE i.user_id = $1
                    ORDER BY i.created_at DESC
                    LIMIT 50
                """,
                "params": {"1": 1}
            },
            
            # Notifications queries
            {
                "name": "User Notifications (Unread)",
                "query": """
                    SELECT n.*
                    FROM notifications n
                    WHERE n.user_id = $1
                    AND n.is_read = false
                    ORDER BY n.created_at DESC
                    LIMIT 20
                """,
                "params": {"1": 1}
            },
            
            # Admin queries
            {
                "name": "Reports Queue (Admin)",
                "query": """
                    SELECT r.*, p1.name as reporter_name, p2.name as reported_name
                    FROM reports r
                    JOIN profiles p1 ON r.reporter_id = p1.user_id
                    JOIN profiles p2 ON r.reported_user_id = p2.user_id
                    WHERE r.status = 'pending'
                    ORDER BY r.created_at ASC
                    LIMIT 50
                """,
                "params": {}
            },
            
            # Analytics queries
            {
                "name": "Daily Active Users",
                "query": """
                    SELECT DATE(last_active_at) as date, COUNT(*) as dau
                    FROM user_activity
                    WHERE last_active_at >= CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY DATE(last_active_at)
                    ORDER BY date DESC
                    LIMIT 30
                """,
                "params": {}
            }
        ]
        
        # Run all tests
        for test in test_queries:
            print(f"\n🔍 Testing: {test['name']}")
            result = await self.test_query(test['name'], test['query'], test.get('params'))
            self.results.append(result)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"✅ Execution Time: {result['execution_time']:.3f}s")
                print(f"📊 Total Cost: {result['total_cost']}")
                print(f"⏱️  Actual Time: {result['actual_time']:.3f}ms")
                print(f"📈 Rows Returned: {result['rows_returned']}")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate performance report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE REPORT")
        print("=" * 60)
        
        successful_tests = [r for r in self.results if 'error' not in r]
        failed_tests = [r for r in self.results if 'error' in r]
        
        print(f"✅ Successful Tests: {len(successful_tests)}")
        print(f"❌ Failed Tests: {len(failed_tests)}")
        
        if successful_tests:
            avg_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests)
            print(f"⏱️  Average Execution Time: {avg_time:.3f}s")
            
            # Find slowest queries
            slowest = sorted(successful_tests, key=lambda x: x['execution_time'], reverse=True)[:3]
            print(f"\n🐌 Slowest Queries:")
            for i, test in enumerate(slowest, 1):
                print(f"  {i}. {test['name']}: {test['execution_time']:.3f}s")
        
        if failed_tests:
            print(f"\n❌ Failed Queries:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['error']}")
        
        # Performance recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("  - Monitor slow queries (>1s execution time)")
        print("  - Consider additional indexes for complex WHERE clauses")
        print("  - Use connection pooling for high concurrency")
        print("  - Consider read replicas for analytics queries")


async def main():
    """Main function."""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost:5432/dating")
    
    tester = QueryPerformanceTester(database_url)
    
    try:
        await tester.connect()
        await tester.run_performance_tests()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
