"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import StaffHeader from "@/components/staff-header"
import { fetchDoctorQueue, completeConsultation } from "@/lib/api"
import type { Patient } from "@/types/staff"

export default function DoctorPortal() {
  const [queue, setQueue] = useState<Patient[]>([])
  const [currentPatient, setCurrentPatient] = useState<Patient | null>(null)
  const [prescription, setPrescription] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadQueue()

    // Set up SSE for real-time updates
    const eventSource = new EventSource("/api/events/doctor-queue")

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setQueue(data)
    }

    return () => {
      eventSource.close()
    }
  }, [])

  const loadQueue = async () => {
    try {
      const data = await fetchDoctorQueue()
      setQueue(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load patient queue",
        variant: "destructive",
      })
    }
  }

  const handleStartConsultation = (patient: Patient) => {
    setCurrentPatient(patient)
    setPrescription("")
  }

  const handleCompleteConsultation = async () => {
    if (!currentPatient) return

    try {
      setIsLoading(true)
      await completeConsultation({
        patientId: currentPatient.id,
        prescription: prescription,
      })

      toast({
        title: "Consultation Complete",
        description: `Patient ${currentPatient.id} moved to pharmacy queue`,
      })

      setCurrentPatient(null)
      setPrescription("")
      setIsDialogOpen(false)

      // Refresh queue
      loadQueue()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to complete consultation",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <StaffHeader role="Doctor" />

      <main className="container mx-auto px-4 py-6">
        <Tabs defaultValue="queue" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="queue">Patient Queue</TabsTrigger>
            <TabsTrigger value="current">Current Patient</TabsTrigger>
          </TabsList>

          <TabsContent value="queue" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Your Patient Queue</CardTitle>
                <CardDescription>Patients waiting for consultation</CardDescription>
              </CardHeader>
              <CardContent>
                {queue.length === 0 ? (
                  <p className="text-center py-6 text-gray-500">No patients currently waiting</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Name</TableHead>
                        <TableHead>Queue Position</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {queue.map((patient) => (
                        <TableRow key={patient.id}>
                          <TableCell className="font-medium">{patient.id}</TableCell>
                          <TableCell>{patient.name}</TableCell>
                          <TableCell>{patient.queuePosition}</TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              onClick={() => handleStartConsultation(patient)}
                              disabled={currentPatient !== null}
                            >
                              Start Consultation
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="current">
            <Card>
              <CardHeader>
                <CardTitle>Current Patient</CardTitle>
                <CardDescription>Patient currently in consultation</CardDescription>
              </CardHeader>
              <CardContent>
                {!currentPatient ? (
                  <div className="text-center py-12">
                    <p className="text-gray-500 mb-4">No patient currently in consultation</p>
                    <Button variant="outline" onClick={() => loadQueue()}>
                      Check Queue
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Patient ID</h3>
                        <p className="text-lg font-semibold">{currentPatient.id}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Patient Name</h3>
                        <p className="text-lg font-semibold">{currentPatient.name}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Contact</h3>
                        <p className="text-lg font-semibold">{currentPatient.contact || "N/A"}</p>
                      </div>
                      <div>
                        <h3 className="text-sm font-medium text-gray-500">Wait Time</h3>
                        <p className="text-lg font-semibold">{currentPatient.waitTime || "0"} minutes</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="prescription">Prescription</Label>
                      <Textarea
                        id="prescription"
                        placeholder="Enter prescription details..."
                        value={prescription}
                        onChange={(e) => setPrescription(e.target.value)}
                        rows={5}
                      />
                    </div>

                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setCurrentPatient(null)
                          setPrescription("")
                        }}
                      >
                        Cancel
                      </Button>
                      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                          <Button>Complete & Send to Pharmacy</Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Confirm Completion</DialogTitle>
                            <DialogDescription>
                              This will complete the consultation and send the patient to the pharmacy queue.
                            </DialogDescription>
                          </DialogHeader>
                          <div className="py-4">
                            <h4 className="font-medium mb-2">Prescription:</h4>
                            <p className="text-sm bg-gray-100 dark:bg-gray-800 p-3 rounded">
                              {prescription || "No prescription added"}
                            </p>
                          </div>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                              Cancel
                            </Button>
                            <Button onClick={handleCompleteConsultation} disabled={isLoading}>
                              {isLoading ? "Processing..." : "Confirm"}
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

