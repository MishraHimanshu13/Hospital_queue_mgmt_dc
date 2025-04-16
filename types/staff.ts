export interface Patient {
  id: string
  name: string
  contact?: string
  assignedDoctor?: string
  queuePosition: number
  estimatedWaitTime?: number
  waitTime?: number
  prescription?: string
}

export interface Doctor {
  id: string
  name: string
  specialty: string
  queueLength: number
}

export interface StaffMember {
  id: string
  name: string
  username: string
  role: string
  active: boolean
}

export interface QueueStatus {
  name: string
  patientsWaiting: number
  averageWaitTime: number
  status: "Normal" | "Busy" | "Overloaded"
}

export interface SystemStats {
  totalPatientsToday: number
  activePatients: number
  averageWaitTime: number
  systemStatus: string
  queues: QueueStatus[]
}

