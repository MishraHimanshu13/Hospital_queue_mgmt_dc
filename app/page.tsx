import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-blue-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-blue-700 dark:text-blue-400 mb-4">Hospital Queue Management System</h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            A comprehensive solution for managing patient queues across different hospital departments
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card className="shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader>
              <CardTitle>Patient Portal</CardTitle>
              <CardDescription>Track your queue position</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Enter your 4-digit ID to check your current queue status and assigned doctor.
              </p>
            </CardContent>
            <CardFooter>
              <Link href="/patient" className="w-full">
                <Button className="w-full bg-blue-600 hover:bg-blue-700">Access Portal</Button>
              </Link>
            </CardFooter>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader>
              <CardTitle>Receptionist</CardTitle>
              <CardDescription>Patient registration</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Register new patients, generate IDs, and assign to doctor queues.
              </p>
            </CardContent>
            <CardFooter>
              <Link href="/staff/receptionist" className="w-full">
                <Button className="w-full bg-green-600 hover:bg-green-700">Staff Login</Button>
              </Link>
            </CardFooter>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader>
              <CardTitle>Doctor Portal</CardTitle>
              <CardDescription>Patient consultation</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                View your patient queue, prescribe medicines, and send to pharmacy.
              </p>
            </CardContent>
            <CardFooter>
              <Link href="/staff/doctor" className="w-full">
                <Button className="w-full bg-purple-600 hover:bg-purple-700">Staff Login</Button>
              </Link>
            </CardFooter>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader>
              <CardTitle>Pharmacy</CardTitle>
              <CardDescription>Medicine dispensing</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                View pharmacy queue, dispense medicines, and check out patients.
              </p>
            </CardContent>
            <CardFooter>
              <Link href="/staff/pharmacy" className="w-full">
                <Button className="w-full bg-amber-600 hover:bg-amber-700">Staff Login</Button>
              </Link>
            </CardFooter>
          </Card>

          <Card className="shadow-lg hover:shadow-xl transition-shadow">
            <CardHeader>
              <CardTitle>Admin Portal</CardTitle>
              <CardDescription>System management</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Manage staff accounts, monitor system health, and configure settings.
              </p>
            </CardContent>
            <CardFooter>
              <Link href="/staff/admin" className="w-full">
                <Button className="w-full bg-red-600 hover:bg-red-700">Admin Login</Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  )
}

