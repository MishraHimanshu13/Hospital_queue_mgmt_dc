"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchPatientStatus } from "@/lib/api"
import type { PatientStatus } from "@/types/patient"
import QueueDisplay from "@/components/queue-display"

export default function PatientQueueStatus() {
  const { id } = useParams()
  const [status, setStatus] = useState<PatientStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Initial fetch
    getPatientStatus()

    // Set up SSE for real-time updates
    const eventSource = new EventSource(`/api/events/patient/${id}`)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setStatus(data)
    }

    eventSource.onerror = () => {
      eventSource.close()
      setError("Connection to server lost. Please refresh the page.")
    }

    return () => {
      eventSource.close()
    }
  }, [id])

  const getPatientStatus = async () => {
    try {
      setLoading(true)
      const data = await fetchPatientStatus(id as string)
      setStatus(data)
      setError(null)
    } catch (err) {
      setError("Patient ID not found or system error")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-700 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-300">Loading your queue status...</p>
        </div>
      </div>
    )
  }

  if (error || !status) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50 dark:bg-gray-900 p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl text-red-600">Error</CardTitle>
            <CardDescription>{error || "Unknown error occurred"}</CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="mb-4">Please check your ID and try again, or contact reception for assistance.</p>
            <p className="text-sm text-gray-500">Patient ID: {id}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-blue-50 dark:bg-gray-900 p-4">
      <div className="container mx-auto max-w-2xl">
        <Card className="shadow-xl">
          <CardHeader className="text-center border-b">
            <div className="flex justify-between items-center mb-2">
              <Badge variant={getStatusVariant(status.stage)}>{status.stage}</Badge>
              <p className="text-sm text-gray-500">ID: {id}</p>
            </div>
            <CardTitle className="text-2xl text-blue-700 dark:text-blue-400">{status.patientName}</CardTitle>
            <CardDescription>{getStageMessage(status.stage)}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <QueueDisplay
              queuePosition={status.queuePosition}
              totalInQueue={status.totalInQueue}
              estimatedWaitTime={status.estimatedWaitTime}
              stage={status.stage}
              assignedDoctor={status.assignedDoctor}
              assignedCounter={status.assignedCounter}
              prescriptions={status.prescriptions}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function getStatusVariant(stage: string): "default" | "secondary" | "destructive" | "outline" {
  switch (stage) {
    case "Waiting for Doctor":
      return "default"
    case "In Consultation":
      return "secondary"
    case "Ready for Pharmacy":
      return "outline"
    case "Checked Out":
      return "destructive"
    default:
      return "default"
  }
}

function getStageMessage(stage: string): string {
  switch (stage) {
    case "Waiting for Doctor":
      return "Please wait until your number is called"
    case "In Consultation":
      return "You are currently with the doctor"
    case "Ready for Pharmacy":
      return "Please proceed to the pharmacy queue"
    case "Checked Out":
      return "Your visit is complete. Thank you!"
    default:
      return "Unknown status"
  }
}

