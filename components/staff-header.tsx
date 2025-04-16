"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { useToast } from "@/hooks/use-toast"
import { logoutUser } from "@/lib/auth"

interface StaffHeaderProps {
  role: string
}

export default function StaffHeader({ role }: StaffHeaderProps) {
  const router = useRouter()
  const { toast } = useToast()

  const handleLogout = async () => {
    await logoutUser()
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    })
    router.push("/staff/login")
  }

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
              {role.charAt(0)}
            </div>
            <div>
              <h1 className="font-bold text-lg">{role} Portal</h1>
              <p className="text-sm text-gray-500">Hospital Queue Management System</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/">
              <Button variant="ghost" size="sm">
                Home
              </Button>
            </Link>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

