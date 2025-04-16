"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/hooks/use-toast"
import StaffHeader from "@/components/staff-header"
import { fetchDoctors, registerPatient, fetchWaitingPatients } from "@/lib/api"
import type { Doctor, Patient } from "@/types/staff"

export default function ReceptionistPortal() {
  const [patientName, setPatientName] = useState("")
  const [patientContact, setPatientContact] = useState("")
  const [selectedDoctor, setSelectedDoctor] = useState("")
  const [generatedId, setGeneratedId] = useState<string | null>(null)
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [waitingPatients, setWaitingPatients] = useState<Patient[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadDoctors()
    loadWaitingPatients()

    // Set up SSE for real-time updates
    const eventSource = new EventSource("/api/events/waiting-patients")

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setWaitingPatients(data)
    }

    return () => {
      eventSource.close()
    }
  }, [])

  const loadDoctors = async () => {
    try {
      const data = await fetchDoctors()
      setDoctors(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load doctors",
        variant: "destructive",
      })
    }
  }

  const loadWaitingPatients = async () => {
    try {
      const data = await fetchWaitingPatients()
      setWaitingPatients(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load waiting patients",
        variant: "destructive",
      })
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!patientName || !patientContact || !selectedDoctor) {
      toast({
        title: "Missing fields",
        description: "Please fill in all fields",
        variant: "destructive",
      })
      return
    }

    try {
      setIsLoading(true)
      const data = await registerPatient({
        name: patientName,
        contact: patientContact,
        doctorId: selectedDoctor,
      })

      setGeneratedId(data.patientId)
      toast({
        title: "Patient Registered",
        description: `ID: ${data.patientId} assigned to ${data.doctorName}`,
      })

      // Reset form
      setPatientName("")
      setPatientContact("")
      setSelectedDoctor("")

      // Refresh waiting patients list
      loadWaitingPatients()
    } catch (error) {
      toast({
        title: "Registration Failed",
        description: "Could not register patient",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <StaffHeader role="Receptionist" />

      <main className="container mx-auto px-4 py-6">
        <Tabs defaultValue="register" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="register">Register Patient</TabsTrigger>
            <TabsTrigger value="waiting">Waiting Patients</TabsTrigger>
          </TabsList>

          <TabsContent value="register" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Patient Registration</CardTitle>
                <CardDescription>Register a new patient and assign to a doctor</CardDescription>
              </CardHeader>
              <form onSubmit={handleRegister}>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="patientName">Patient Name</Label>
                    <Input
                      id="patientName"
                      placeholder="Enter patient name"
                      value={patientName}
                      onChange={(e) => setPatientName(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="patientContact">Contact Number</Label>
                    <Input
                      id="patientContact"
                      placeholder="Enter contact number"
                      value={patientContact}
                      onChange={(e) => setPatientContact(e.target.value)}
                      disabled={isLoading}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="doctor">Assign Doctor</Label>
                    <Select value={selectedDoctor} onValueChange={setSelectedDoctor} disabled={isLoading}>
                      <SelectTrigger id="doctor">
                        <SelectValue placeholder="Select a doctor" />
                      </SelectTrigger>
                      <SelectContent>
                        {doctors.map((doctor) => (
                          <SelectItem key={doctor.id} value={doctor.id}>
                            {doctor.name} ({doctor.queueLength} patients waiting)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-between">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setPatientName("")
                      setPatientContact("")
                      setSelectedDoctor("")
                      setGeneratedId(null)
                    }}
                  >
                    Clear
                  </Button>
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? "Registering..." : "Register Patient"}
                  </Button>
                </CardFooter>
              </form>
            </Card>

            {generatedId && (
              <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                <CardContent className="p-6">
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-green-800 dark:text-green-300 mb-2">
                      Patient Successfully Registered
                    </h3>
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-4 inline-block">
                      <p className="text-sm text-gray-500 dark:text-gray-400">Patient ID</p>
                      <p className="text-4xl font-bold">{generatedId}</p>
                    </div>
                    <p className="text-sm">
                      Please inform the patient to keep this ID for tracking their queue status.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="waiting">
            <Card>
              <CardHeader>
                <CardTitle>Waiting Patients</CardTitle>
                <CardDescription>Patients currently waiting to see doctors</CardDescription>
              </CardHeader>
              <CardContent>
                {waitingPatients.length === 0 ? (
                  <p className="text-center py-6 text-gray-500">No patients currently waiting</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Assigned Doctor</TableHead>
                        <TableHead>Queue Position</TableHead>
                        <TableHead>Wait Time</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {waitingPatients.map((patient) => (
                        <TableRow key={patient.id}>
                          <TableCell className="font-medium">{patient.id}</TableCell>
                          <TableCell>{patient.name}</TableCell>
                          <TableCell>{patient.assignedDoctor}</TableCell>
                          <TableCell>{patient.queuePosition}</TableCell>
                          <TableCell>{patient.estimatedWaitTime} mins</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

