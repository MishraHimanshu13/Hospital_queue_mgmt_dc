"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"

export default function PatientPortal() {
  const [patientId, setPatientId] = useState("")
  const router = useRouter()
  const { toast } = useToast()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (patientId.length !== 4 || !/^\d+$/.test(patientId)) {
      toast({
        title: "Invalid ID",
        description: "Please enter a valid 4-digit ID",
        variant: "destructive",
      })
      return
    }

    router.push(`/patient/queue/${patientId}`)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-blue-50 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl text-blue-700 dark:text-blue-400">Patient Queue Portal</CardTitle>
          <CardDescription>Enter your 4-digit ID to check your queue status</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Enter your 4-digit ID (e.g., 3892)"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  maxLength={4}
                  className="text-center text-2xl py-6"
                />
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">
              Check Queue Status
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}

