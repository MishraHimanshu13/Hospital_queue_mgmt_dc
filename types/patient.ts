export interface PatientStatus {
  patientName: string
  stage: "Waiting for Doctor" | "In Consultation" | "Ready for Pharmacy" | "Checked Out"
  queuePosition: number
  totalInQueue: number
  estimatedWaitTime: number
  assignedDoctor?: string
  assignedCounter?: number
  prescriptions?: string[]
}

