import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Workflow, Mail, ArrowLeft, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ForgotPasswordFormData {
  email: string;
}

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isEmailSent, setIsEmailSent] = useState(false);
  const [, setLocation] = useLocation();

  const form = useForm<ForgotPasswordFormData>({
    defaultValues: {
      email: "",
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true);
    try {
      // Mock API call - replace with actual forgot password logic
      console.log("Forgot password request:", data);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Show success state
      setIsEmailSent(true);

      // Redirect to OTP verification after a short delay
      setTimeout(() => {
        setLocation(`/verify-otp?email=${encodeURIComponent(data.email)}`);
      }, 2000);
    } catch (error) {
      console.error("Forgot password error:", error);
      form.setError("root", {
        message: "Failed to send reset email. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isEmailSent) {
    return (
      <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
        <div className="w-full max-w-md mx-auto pb-8">
          {/* Success Card */}
          <Card className="border-2 border-green-200 shadow-2xl bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-6">
              <div className="flex flex-col items-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg mb-3">
                  <Mail className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
              </div>
              <CardTitle className="text-2xl font-semibold text-text-dark">
                Check your email
              </CardTitle>
              <CardDescription className="text-gray-600">
                We've sent a reset code to your email address
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                  <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Redirecting you to verification page...
                </p>
                <Link href="/login">
                  <Button variant="outline" className="border-gray-200 hover:border-coral hover:bg-coral hover:text-white">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Login
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
      <div className="w-full max-w-md mx-auto pb-8">
        {/* Forgot Password Card */}
        <Card className="border-2 border-gray-200 shadow-2xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex flex-col items-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-coral to-coral-600 rounded-xl shadow-lg mb-3">
                <Workflow className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
            </div>
            <CardTitle className="text-2xl font-semibold text-text-dark">
              Forgot your password?
            </CardTitle>
            <CardDescription className="text-gray-600">
              Enter your email address and we'll send you a reset code
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                {/* Email Field */}
                <FormField
                  control={form.control}
                  name="email"
                  rules={{
                    required: "Email is required",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Invalid email address",
                    },
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-sm font-medium text-gray-700">
                        Email address
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <Input
                            {...field}
                            type="email"
                            placeholder="Enter your email"
                            className={cn(
                              "pl-11 h-12 border-2 border-gray-200 rounded-xl",
                              "focus:border-coral focus:ring-0 focus:outline-none",
                              "transition-all duration-200",
                              "hover:border-gray-300"
                            )}
                            disabled={isLoading}
                          />
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
                      Sending reset code...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Send Reset Code
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </div>
                  )}
                </Button>
              </form>
            </Form>

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
