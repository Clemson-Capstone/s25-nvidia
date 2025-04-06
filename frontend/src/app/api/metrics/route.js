import { NextResponse } from 'next/server';
import { register } from '../../../lib/metrics';

export const dynamic = 'force-dynamic'; // Ensure the route is not statically optimized

export async function GET() {
  try {
    // Set the correct content type for Prometheus
    const headers = {
      'Content-Type': register.contentType
    };
    
    // Get the metrics as a string
    const metrics = await register.metrics();
    
    // Send the metrics
    return new NextResponse(metrics, { 
      status: 200,
      headers: headers
    });
  } catch (error) {
    console.error('Error generating metrics:', error);
    return new NextResponse('Error generating metrics', { status: 500 });
  }
}