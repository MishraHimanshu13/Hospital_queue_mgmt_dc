import { Progress } from "@/components/ui/progress"
import { Card, CardContent } from "@/components/ui/card"

interface QueueDisplayProps {
  queuePosition: number
  totalInQueue: number
  estimatedWaitTime: number
  stage: string
  assignedDoctor?: string
  assignedCounter?: number
  prescriptions?: string[]
}

export default function QueueDisplay({
  queuePosition,
  totalInQueue,
  estimatedWaitTime,
  stage,
  assignedDoctor,
  assignedCounter,
  prescriptions,
}: QueueDisplayProps) {
  const progressPercentage = totalInQueue > 0 ? Math.max(0, 100 - (queuePosition / totalInQueue) * 100) : 100

  return (
    <div className="space-y-6">
      {stage !== "Checked Out" && (
        <>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Queue Position</span>
              <span className="font-medium">
                {queuePosition} of {totalInQueue}
              </span>
            </div>
            <Progress value={progressPercentage} className="h-2" />
            <p className="text-sm text-gray-500 text-right">Estimated wait: ~{estimatedWaitTime} minutes</p>
          </div>

          {assignedDoctor && (
            <Card className="bg-blue-50 dark:bg-gray-800 border-blue-200 dark:border-gray-700">
              <CardContent className="p-4">
                <div className="flex items-center space-x-4">
                  <div className="h-10 w-10 rounded-full bg-blue-200 dark:bg-blue-900 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-6 w-6 text-blue-700 dark:text-blue-300"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium">Assigned Doctor</p>
                    <p className="text-lg">{assignedDoctor}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {stage === "Ready for Pharmacy" && (
        <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <CardContent className="p-4">
            <div className="flex items-center space-x-4">
              <div className="h-10 w-10 rounded-full bg-green-200 dark:bg-green-800 flex items-center justify-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6 text-green-700 dark:text-green-300"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1M19 20a2 2 0 002-2V8a2 2 0 00-2-2h-5M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium">Pharmacy Queue</p>
                <p className="text-lg">
                  Position: {queuePosition} {assignedCounter && `• Counter: ${assignedCounter}`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {stage === "Checked Out" && prescriptions && prescriptions.length > 0 && (
        <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <CardContent className="p-4">
            <h3 className="font-medium mb-2">Your Prescriptions</h3>
            <ul className="list-disc list-inside space-y-1">
              {prescriptions.map((med, index) => (
                <li key={index} className="text-sm">
                  {med}
                </li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">
              Thank you for your visit. Please follow your prescription instructions carefully.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

