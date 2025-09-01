import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Workflow, Eye, EyeOff, Mail, Lock, User, ArrowRight, Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface SignupFormData {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();

  const form = useForm<SignupFormData>({
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
    },
  });

  const onSubmit = async (data: SignupFormData) => {
    setIsLoading(true);
    try {
      // Mock signup - replace with actual registration logic
      console.log("Signup attempt:", data);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Redirect to login on success
      setLocation("/login?message=Account created successfully");
    } catch (error) {
      console.error("Signup error:", error);
      form.setError("root", {
        message: "Failed to create account. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const password = form.watch("password");

  return (
    <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
      <div className="w-full max-w-md mx-auto pb-8">
        {/* Signup Card */}
        <Card className="border-2 border-gray-200 shadow-2xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex flex-col items-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-coral to-coral-600 rounded-xl shadow-lg mb-3">
                <Workflow className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
            </div>
            <CardTitle className="text-2xl font-semibold text-text-dark">
              Create your account
            </CardTitle>
            <CardDescription className="text-gray-600">
              Get started with FlowForge today
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                {/* Full Name Field */}
                <FormField
                  control={form.control}
                  name="fullName"
                  rules={{
                    required: "Full name is required",
                    minLength: {
                      value: 2,
                      message: "Name must be at least 2 characters",
                    },
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-sm font-medium text-gray-700">
                        Full name
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <Input
                            {...field}
                            type="text"
                            placeholder="Enter your full name"
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

                {/* Password Field */}
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
                        Password
                      </FormLabel>
                      <FormControl>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                          <Input
                            {...field}
                            type={showPassword ? "text" : "password"}
                            placeholder="Create a strong password"
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
                            placeholder="Confirm your password"
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

                {/* Terms of Service Checkbox */}
                <FormField
                  control={form.control}
                  name="acceptTerms"
                  rules={{
                    required: "You must accept the terms and conditions",
                  }}
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                          disabled={isLoading}
                          className="mt-1 border-2 border-gray-300 data-[state=checked]:bg-coral data-[state=checked]:border-coral"
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none">
                        <FormLabel className="text-sm text-gray-700 cursor-pointer">
                          I agree to the{" "}
                          <Link href="/terms">
                            <button className="text-coral hover:text-coral-600 underline underline-offset-2 transition-colors">
                              Terms of Service
                            </button>
                          </Link>{" "}
                          and{" "}
                          <Link href="/privacy">
                            <button className="text-coral hover:text-coral-600 underline underline-offset-2 transition-colors">
                              Privacy Policy
                            </button>
                          </Link>
                        </FormLabel>
                        <FormMessage />
                      </div>
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
                      Creating account...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Create Account
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </div>
                  )}
                </Button>
              </form>
            </Form>

            {/* Password Requirements */}
            <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg">
              <p className="font-medium mb-2">Password requirements:</p>
              <div className="space-y-1">
                <div className="flex items-center">
                  <Check className="w-3 h-3 text-green-600 mr-2" />
                  <span>At least 8 characters</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-3 h-3 text-green-600 mr-2" />
                  <span>One uppercase letter</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-3 h-3 text-green-600 mr-2" />
                  <span>One lowercase letter</span>
                </div>
                <div className="flex items-center">
                  <Check className="w-3 h-3 text-green-600 mr-2" />
                  <span>One number</span>
                </div>
              </div>
            </div>

            {/* Additional Links */}
            <div className="space-y-4 text-center">
              <div className="flex items-center justify-center space-x-1">
                <span className="text-sm text-gray-600">Already have an account?</span>
                <Link href="/login">
                  <button className="text-sm font-medium text-coral hover:text-coral-600 transition-colors underline underline-offset-2">
                    Sign in
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
