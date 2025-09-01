import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation } from "wouter";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Workflow, Eye, EyeOff, Mail, Lock, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoginFormData {
  email: string;
  password: string;
}

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [, setLocation] = useLocation();

  const form = useForm<LoginFormData>({
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      // Mock login - replace with actual authentication logic
      console.log("Login attempt:", data);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Redirect to dashboard on success
      setLocation("/");
    } catch (error) {
      console.error("Login error:", error);
      form.setError("root", {
        message: "Invalid email or password. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-light-grey via-white to-coral-50 py-8 px-4 overflow-y-auto">
      <div className="w-full max-w-md mx-auto pb-8">
        {/* Login Card */}
        <Card className="border-2 border-gray-200 shadow-2xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-6">
            <div className="flex flex-col items-center mb-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-coral to-coral-600 rounded-xl shadow-lg mb-3">
                <Workflow className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-text-dark mb-1">FlowForge</h1>
            </div>
            <CardTitle className="text-2xl font-semibold text-text-dark">
              Welcome back
            </CardTitle>
            <CardDescription className="text-gray-600">
              Sign in to your account to continue
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

                {/* Password Field */}
                <FormField
                  control={form.control}
                  name="password"
                  rules={{
                    required: "Password is required",
                    minLength: {
                      value: 6,
                      message: "Password must be at least 6 characters",
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
                            placeholder="Enter your password"
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
                      Signing in...
                    </div>
                  ) : (
                    <div className="flex items-center">
                      Sign In
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </div>
                  )}
                </Button>
              </form>
            </Form>

            {/* Additional Links */}
            <div className="space-y-4 text-center">
              <div className="flex items-center justify-center space-x-1">
                <span className="text-sm text-gray-600">Don't have an account?</span>
                <Link href="/signup">
                  <button className="text-sm font-medium text-coral hover:text-coral-600 transition-colors underline underline-offset-2">
                    Sign up
                  </button>
                </Link>
              </div>

              <div>
                <Link href="/forgot-password">
                  <button className="text-sm text-coral hover:text-coral-600 transition-colors underline underline-offset-2">
                    Forgot your password?
                  </button>
                </Link>
              </div>
            </div>

            {/* Demo Credentials */}
            <div className="border-t border-gray-200 pt-6">
              <p className="text-xs text-gray-500 text-center mb-3 font-medium">
                Demo Credentials
              </p>
              <div className="space-y-2 text-xs text-gray-600 bg-gray-50 p-3 rounded-lg">
                <div className="flex justify-between">
                  <span>Email:</span>
                  <span className="font-mono">demo@flowforge.com</span>
                </div>
                <div className="flex justify-between">
                  <span>Password:</span>
                  <span className="font-mono">demo123</span>
                </div>
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
