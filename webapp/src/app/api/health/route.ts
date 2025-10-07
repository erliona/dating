import { NextResponse } from "next/server";

/**
 * Health Check Endpoint
 *
 * Returns the health status of the webapp.
 * Used by monitoring systems and load balancers.
 *
 * GET /api/health
 */
export async function GET() {
  return NextResponse.json(
    {
      status: "healthy",
      service: "webapp",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    },
    { status: 200 }
  );
}
