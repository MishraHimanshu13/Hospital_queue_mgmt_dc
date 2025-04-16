import type { NextRequest } from "next/server"
import { fetchPharmacyQueue } from "@/lib/api"

export async function GET(request: NextRequest) {
  // Set headers for SSE
  const headers = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  }

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      // Send initial data
      try {
        const initialData = await fetchPharmacyQueue()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(initialData)}\n\n`))
      } catch (error) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify([])}\n\n`))
      }

      // Simulate updates every 5 seconds
      const interval = setInterval(async () => {
        try {
          const data = await fetchPharmacyQueue()
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`))
        } catch (error) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify([])}\n\n`))
        }
      }, 5000)

      // Clean up on close
      request.signal.addEventListener("abort", () => {
        clearInterval(interval)
        controller.close()
      })
    },
  })

  return new Response(stream, { headers })
}

