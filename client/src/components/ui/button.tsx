import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-coral/20 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-coral text-white hover:bg-coral/90 hover:shadow-md active:scale-[0.98]",
        destructive:
          "bg-red-500 text-white hover:bg-red-600 hover:shadow-md active:scale-[0.98]",
        outline:
          "border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 active:scale-[0.98]",
        secondary:
          "bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-sm active:scale-[0.98]",
        ghost: "text-gray-700 hover:bg-gray-100 hover:text-gray-900 active:scale-[0.98]",
        link: "text-coral underline-offset-4 hover:underline hover:text-coral/80",
      },
      size: {
        default: "h-11 px-6 py-3",
        sm: "h-9 rounded-md px-4 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-11 w-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
