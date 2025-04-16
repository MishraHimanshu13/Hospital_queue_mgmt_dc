import type { NextRequest } from "next/server"
import { fetchSystemStats } from "@/lib/api"

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
        const initialData = await fetchSystemStats()
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(initialData)}\n\n`))
      } catch (error) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({})}\n\n`))
      }

      // Simulate updates every 10 seconds
      const interval = setInterval(async () => {
        try {
          const data = await fetchSystemStats()
          // Simulate some random changes to the data
          data.activePatients = Math.max(0, data.activePatients + Math.floor(Math.random() * 3) - 1)
          data.averageWaitTime = Math.max(5, data.averageWaitTime + Math.floor(Math.random() * 5) - 2)
          data.queues.forEach((queue) => {
            queue.patientsWaiting = Math.max(0, queue.patientsWaiting + Math.floor(Math.random() * 3) - 1)
            queue.averageWaitTime = Math.max(0, queue.averageWaitTime + Math.floor(Math.random() * 5) - 2)
            queue.status = queue.patientsWaiting > 10 ? "Overloaded" : queue.patientsWaiting > 5 ? "Busy" : "Normal"
          })

          controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`))
        } catch (error) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({})}\n\n`))
        }
      }, 10000)

      // Clean up on close
      request.signal.addEventListener("abort", () => {
        clearInterval(interval)
        controller.close()
      })
    },
  })

  return new Response(stream, { headers })
}

