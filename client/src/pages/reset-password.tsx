import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Workflow, Lock, Eye, EyeOff, ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface ResetPasswordFormData {
  password: string;
  confirmPassword: string;
}

export default function ResetPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [, setLocation] = useLocation();

  const form = useForm<ResetPasswordFormData>({
    defaultValues: {
      password: "",
      confirmPassword: "",
    },
  });

  // Get token from URL params
  const searchParams = new URLSearchParams(window.location.search);
  const email = searchParams.get('email') || '';
  const token = searchParams.get('token') || '';

  const password = form.watch("password");

  const getPasswordStrength = (password: string) => {
    const requirements = [
      { test: password.length >= 8, label: "At least 8 characters" },
      { test: /[a-z]/.test(password), label: "One lowercase letter" },
      { test: /[A-Z]/.test(password), label: "One uppercase letter" },
      { test: /\d/.test(password), label: "One number" },
    ];

    const passed = requirements.filter(req => req.test).length;
    return { requirements, passed, total: requirements.length };
  };

  const passwordStrength = getPasswordStrength(password);

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsLoading(true);
    try {
      console.log("Reset password:", { email, token, ...data });

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Show success state
      setIsSuccess(true);

      // Redirect to login after a short delay
      setTimeout(() => {
        setLocation("/login?message=Password reset successfully");
      }, 3000);
    } catch (error) {
      console.error("Reset password error:", error);
      form.setError("root", {
        message: "Failed to reset password. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
        <div className="w-full max-w-md mx-auto pb-8">
          {/* Success Card */}
          <Card className="border-2 border-green-200 shadow-2xl bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-6">
              <div className="flex flex-col items-center mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-lg mb-3">
                  <Check className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
              </div>
              <CardTitle className="text-2xl font-semibold text-text-dark">
                Password reset successful!
              </CardTitle>
              <CardDescription className="text-gray-600">
                Your password has been updated successfully
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-6">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                  <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  Redirecting you to login page...
                </p>
                <Link href="/login">
                  <Button className="bg-coral hover:bg-coral-600">
                    <ArrowRight className="w-4 h-4 mr-2" />
                    Go to Login
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
        {/* Reset Password Card */}
        <Card className="border-2 border-gray-200 shadow-2xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex flex-col items-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-coral to-coral-600 rounded-xl shadow-lg mb-3">
                <Workflow className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
            </div>
            <CardTitle className="text-2xl font-semibold text-text-dark">
              Reset your password
            </CardTitle>
            <CardDescription className="text-gray-600">
              Create a new strong password for your account
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                {/* New Password Field */}
                <FormField
                  control={form.control}
                  name="password"
                  rules={{
                    required: "Password is required",
                    minLength: {
                      value: 8,
                      message: "Password must be at least 8 characters",
                    },
                    pattern: {
                      value: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
                      message: "Password must contain at least one uppercase letter, one lowercase letter, and one number",
                    },
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-sm font-medium text-gray-700">
                        New password
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <Input
                            {...field}
                            type={showPassword ? "text" : "password"}
                            placeholder="Enter new password"
                            className={cn(
                              "pl-11 pr-11 h-12 border-2 border-gray-200 rounded-xl",
                              "focus:border-coral focus:ring-0 focus:outline-none",
                              "transition-all duration-200",
                              "hover:border-gray-300"
                            )}
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                            disabled={isLoading}
                          >
                            {showPassword ? (
                              <EyeOff className="w-5 h-5" />
                            ) : (
                              <Eye className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Confirm Password Field */}
                <FormField
                  control={form.control}
                  name="confirmPassword"
                  rules={{
                    required: "Please confirm your password",
                    validate: (value) =>
                      value === password || "Passwords do not match",
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-sm font-medium text-gray-700">
                        Confirm password
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <Input
                            {...field}
                            type={showConfirmPassword ? "text" : "password"}
                            placeholder="Confirm new password"
                            className={cn(
                              "pl-11 pr-11 h-12 border-2 border-gray-200 rounded-xl",
                              "focus:border-coral focus:ring-0 focus:outline-none",
                              "transition-all duration-200",
                              "hover:border-gray-300"
                            )}
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                            disabled={isLoading}
                          >
                            {showConfirmPassword ? (
                              <EyeOff className="w-5 h-5" />
                            ) : (
                              <Eye className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Password Requirements */}
                {password && (
                  <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl">
                    <p className="text-xs font-medium text-gray-700 mb-3">
                      Password requirements:
                    </p>
                    <div className="space-y-2">
                      {passwordStrength.requirements.map((req, index) => (
                        <div key={index} className="flex items-center text-xs">
                          <Check
                            className={cn(
                              "w-3 h-3 mr-2",
                              req.test ? "text-green-600" : "text-gray-400"
                            )}
                          />
                          <span className={req.test ? "text-green-700" : "text-gray-600"}>
                            {req.label}
                          </span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={cn(
                            "h-2 rounded-full transition-all duration-300",
                            passwordStrength.passed === 4 ? "bg-green-500" :
                            passwordStrength.passed >= 2 ? "bg-yellow-500" : "bg-red-500"
                          )}
                          style={{ width: `${(passwordStrength.passed / passwordStrength.total) * 100}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        Strength: {
                          passwordStrength.passed === 4 ? "Strong" :
                          passwordStrength.passed >= 2 ? "Medium" : "Weak"
                        }
                      </p>
                    </div>
                  </div>
                )}

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
                  disabled={isLoading || passwordStrength.passed < 4}
                >
                  {isLoading ? (
                    <div className="flex items-center">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      Resetting password...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Reset Password
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
