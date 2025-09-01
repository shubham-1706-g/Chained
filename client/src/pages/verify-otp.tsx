import React, { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Workflow, Mail, ArrowLeft, ArrowRight, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface OTPFormData {
  otp: string;
}

export default function VerifyOTPPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const [otpValues, setOtpValues] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [, setLocation] = useLocation();

  const form = useForm<OTPFormData>({
    defaultValues: {
      otp: "",
    },
  });

  // Get email from URL params
  const searchParams = new URLSearchParams(window.location.search);
  const email = searchParams.get('email') || '';

  // Timer for resend OTP
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return; // Only allow single digit

    const newOtpValues = [...otpValues];
    newOtpValues[index] = value;
    setOtpValues(newOtpValues);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Update form value
    const otpString = newOtpValues.join('');
    form.setValue('otp', otpString);
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').slice(0, 6);
    const newOtpValues = [...otpValues];

    for (let i = 0; i < pastedData.length; i++) {
      if (i < 6 && /^\d$/.test(pastedData[i])) {
        newOtpValues[i] = pastedData[i];
      }
    }

    setOtpValues(newOtpValues);
    const otpString = newOtpValues.join('');
    form.setValue('otp', otpString);

    // Focus the next empty input or last input
    const nextEmptyIndex = newOtpValues.findIndex(val => val === '');
    const focusIndex = nextEmptyIndex === -1 ? 5 : nextEmptyIndex;
    inputRefs.current[focusIndex]?.focus();
  };

  const onSubmit = async (data: OTPFormData) => {
    setIsLoading(true);
    try {
      console.log("OTP verification:", data);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Redirect to reset password page
      setLocation(`/reset-password?email=${encodeURIComponent(email)}&token=${data.otp}`);
    } catch (error) {
      console.error("OTP verification error:", error);
      form.setError("root", {
        message: "Invalid verification code. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setIsResending(true);
    try {
      console.log("Resending OTP to:", email);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Reset timer
      setResendTimer(30);
      setOtpValues(['', '', '', '', '', '']);
      form.setValue('otp', '');
      inputRefs.current[0]?.focus();
    } catch (error) {
      console.error("Resend OTP error:", error);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
      <div className="w-full max-w-md mx-auto pb-8">
        {/* OTP Verification Card */}
        <Card className="border-2 border-gray-200 shadow-2xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex flex-col items-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-coral to-coral-600 rounded-xl shadow-lg mb-3">
                <Workflow className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
            </div>
            <CardTitle className="text-2xl font-semibold text-text-dark">
              Verify your email
            </CardTitle>
            <CardDescription className="text-gray-600">
              Enter the 6-digit code sent to {email}
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                {/* OTP Input Fields */}
                <FormField
                  control={form.control}
                  name="otp"
                  rules={{
                    required: "Please enter the verification code",
                    pattern: {
                      value: /^\d{6}$/,
                      message: "Please enter a valid 6-digit code",
                    },
                  }}
                  render={() => (
                    <FormItem>
                      <FormLabel className="text-sm font-medium text-gray-700 text-center block">
                        Verification Code
                      </FormLabel>
                      <FormControl>
                        <div className="flex justify-center space-x-3">
                          {otpValues.map((value, index) => (
                            <input
                              key={index}
                              ref={(el) => (inputRefs.current[index] = el)}
                              type="text"
                              inputMode="numeric"
                              pattern="[0-9]*"
                              maxLength={1}
                              value={value}
                              onChange={(e) => handleOtpChange(index, e.target.value)}
                              onKeyDown={(e) => handleKeyDown(index, e)}
                              onPaste={index === 0 ? handlePaste : undefined}
                              className={cn(
                                "w-12 h-12 text-center text-xl font-semibold border-2 rounded-xl",
                                "focus:border-coral focus:ring-0 focus:outline-none",
                                "transition-all duration-200",
                                "hover:border-gray-300",
                                value ? "border-coral bg-coral/5" : "border-gray-200"
                              )}
                              disabled={isLoading}
                            />
                          ))}
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Error Message */}
                {form.formState.errors.root && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
                    <p className="text-sm text-red-600 font-medium">
                      {form.formState.errors.root.message}
                    </p>
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  className={cn(
                    "w-full h-12 text-base font-medium rounded-xl",
                    "bg-coral hover:bg-coral-600 text-white",
                    "shadow-lg hover:shadow-xl",
                    "transition-all duration-200",
                    "active:scale-[0.98]",
                    isLoading && "opacity-70 cursor-not-allowed"
                  )}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Verifying...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Verify Code
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </div>
                  )}
                </Button>
              </form>
            </Form>

            {/* Resend OTP */}
            <div className="text-center space-y-3">
              <p className="text-sm text-gray-600">
                Didn't receive the code?
              </p>
              <Button
                type="button"
                variant="outline"
                onClick={handleResendOTP}
                disabled={resendTimer > 0 || isResending}
                className={cn(
                  "border-gray-200 hover:border-coral hover:bg-coral hover:text-white",
                  "transition-all duration-200",
                  (resendTimer > 0 || isResending) && "opacity-50 cursor-not-allowed"
                )}
              >
                {isResending ? (
                  <div className="flex items-center">
                    <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mr-2" />
                    Sending...
                  </div>
                ) : resendTimer > 0 ? (
                  <div className="flex items-center">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Resend in {resendTimer}s
                  </div>
                ) : (
                  <div className="flex items-center">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Resend Code
                  </div>
                )}
              </Button>
            </div>

            {/* Additional Links */}
            <div className="space-y-4 text-center">
              <div>
                <Link href="/login">
                  <button className="text-sm text-gray-600 hover:text-gray-800 transition-colors underline underline-offset-2">
                    <ArrowLeft className="w-4 h-4 mr-1 inline" />
                    Back to Login
                  </button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-xs text-gray-500">
            © 2024 FlowForge. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
