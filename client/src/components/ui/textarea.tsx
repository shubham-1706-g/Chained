import * as React from "react"

import { cn } from "@/lib/utils"

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
              className={cn(
          "flex min-h-[100px] w-full rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 transition-all duration-200 ease-in-out hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 resize-none",
          className
        )}
      ref={ref}
      {...props}
    />
  )
})
Textarea.displayName = "Textarea"

export { Textarea }
