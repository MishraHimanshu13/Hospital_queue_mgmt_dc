"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { useToast } from "@/hooks/use-toast"
import StaffHeader from "@/components/staff-header"
import { fetchPharmacyQueue, completePharmacy } from "@/lib/api"
import type { Patient } from "@/types/staff"

export default function PharmacyPortal() {
  const [queue, setQueue] = useState<Patient[]>([])
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadQueue()

    // Set up SSE for real-time updates
    const eventSource = new EventSource("/api/events/pharmacy-queue")

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
      const data = await fetchPharmacyQueue()
      setQueue(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load pharmacy queue",
        variant: "destructive",
      })
    }
  }

  const handleDispenseMedicine = (patient: Patient) => {
    setSelectedPatient(patient)
    setIsDialogOpen(true)
  }

  const handleCompletePharmacy = async () => {
    if (!selectedPatient) return

    try {
      setIsLoading(true)
      await completePharmacy({
        patientId: selectedPatient.id,
      })

      toast({
        title: "Checkout Complete",
        description: `Patient ${selectedPatient.id} has been checked out`,
      })

      setSelectedPatient(null)
      setIsDialogOpen(false)

      // Refresh queue
      loadQueue()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to complete checkout",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <StaffHeader role="Pharmacy" />

      <main className="container mx-auto px-4 py-6">
        <Card>
          <CardHeader>
            <CardTitle>Pharmacy Queue</CardTitle>
            <CardDescription>Patients waiting for medicine dispensing</CardDescription>
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
                    <TableHead>Prescription</TableHead>
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
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            toast({
                              title: "Prescription",
                              description: patient.prescription || "No prescription details",
                            })
                          }}
                        >
                          View
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" onClick={() => handleDispenseMedicine(patient)}>
                          Dispense & Checkout
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </main>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Checkout</DialogTitle>
            <DialogDescription>This will complete the pharmacy process and check out the patient.</DialogDescription>
          </DialogHeader>
          {selectedPatient && (
            <div className="py-4 space-y-4">
              <div>
                <h4 className="font-medium mb-1">Patient:</h4>
                <p>
                  {selectedPatient.name} (ID: {selectedPatient.id})
                </p>
              </div>
              <div>
                <h4 className="font-medium mb-1">Prescription:</h4>
                <p className="text-sm bg-gray-100 dark:bg-gray-800 p-3 rounded">
                  {selectedPatient.prescription || "No prescription details"}
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCompletePharmacy} disabled={isLoading}>
              {isLoading ? "Processing..." : "Confirm Checkout"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

