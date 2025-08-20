import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { User, Bell, Shield, Palette, Download, Upload, Trash2, Key, Globe, ArrowLeft } from "lucide-react";
import { Link } from "wouter";

export default function SettingsPage() {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [pushNotifications, setPushNotifications] = useState(false);
  const [autoSave, setAutoSave] = useState(true);
  const [theme, setTheme] = useState("light");

  return (
    <div className="h-screen bg-light-grey" data-testid="settings-page">
      <div className="h-full overflow-y-auto">
        {/* Header with Back Button */}
      <div className="flex items-center justify-between p-6 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center space-x-6">
          <Link href="/">
            <Button 
              variant="outline" 
              size="lg" 
              className="border-coral text-coral hover:bg-coral hover:text-white transition-colors"
              data-testid="button-back-to-dashboard"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Dashboard
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-text-dark">Settings</h1>
            <p className="text-gray-600 text-lg">Manage your account and application preferences</p>
          </div>
        </div>
      </div>

        <div className="p-6 max-w-6xl mx-auto">
          <div className="space-y-6">
            {/* Profile Settings */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-coral" />
              <CardTitle>Profile Settings</CardTitle>
            </div>
            <CardDescription>Manage your personal information and account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="full-name">Full Name</Label>
                <Input
                  id="full-name"
                  defaultValue="John Doe"
                  className="border-2 border-gray-200 focus:border-coral transition-colors duration-200"
                  data-testid="input-full-name"
                />
              </div>
              <div>
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  defaultValue="john.doe@example.com"
                  className="border-2 border-gray-200 focus:border-coral transition-colors duration-200"
                  data-testid="input-email"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="company">Company (Optional)</Label>
              <Input
                id="company"
                defaultValue="Acme Corp"
                className="border-2 border-gray-200 focus:border-coral transition-colors duration-200"
                data-testid="input-company"
              />
            </div>
            <Button 
              className="bg-coral hover:bg-red-600 text-white transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-lg" 
              data-testid="button-save-profile"
            >
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-coral" />
              <CardTitle>Notifications</CardTitle>
            </div>
            <CardDescription>Configure how you receive notifications about your workflows</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Email Notifications</Label>
                <p className="text-sm text-gray-500">Receive workflow status updates via email</p>
              </div>
              <Switch
                checked={emailNotifications}
                onCheckedChange={setEmailNotifications}
                data-testid="switch-email-notifications"
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Push Notifications</Label>
                <p className="text-sm text-gray-500">Get instant notifications in your browser</p>
              </div>
              <Switch
                checked={pushNotifications}
                onCheckedChange={setPushNotifications}
                data-testid="switch-push-notifications"
              />
            </div>
            <Separator />
            <div>
              <Label>Notification Frequency</Label>
              <Select defaultValue="immediate">
                <SelectTrigger className="w-[200px] mt-2" data-testid="select-notification-frequency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="immediate">Immediate</SelectItem>
                  <SelectItem value="hourly">Hourly Digest</SelectItem>
                  <SelectItem value="daily">Daily Digest</SelectItem>
                  <SelectItem value="never">Never</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Workflow Settings */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Globe className="w-5 h-5 text-coral" />
              <CardTitle>Workflow Preferences</CardTitle>
            </div>
            <CardDescription>Configure default settings for your workflows</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Auto-save Workflows</Label>
                <p className="text-sm text-gray-500">Automatically save changes as you work</p>
              </div>
              <Switch
                checked={autoSave}
                onCheckedChange={setAutoSave}
                data-testid="switch-auto-save"
              />
            </div>
            <Separator />
            <div>
              <Label>Default Execution Timeout</Label>
              <Select defaultValue="300">
                <SelectTrigger className="w-[200px] mt-2" data-testid="select-execution-timeout">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="60">1 minute</SelectItem>
                  <SelectItem value="300">5 minutes</SelectItem>
                  <SelectItem value="900">15 minutes</SelectItem>
                  <SelectItem value="1800">30 minutes</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Error Handling</Label>
              <Select defaultValue="stop">
                <SelectTrigger className="w-[200px] mt-2" data-testid="select-error-handling">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stop">Stop on Error</SelectItem>
                  <SelectItem value="continue">Continue on Error</SelectItem>
                  <SelectItem value="retry">Retry on Error</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Appearance Settings */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Palette className="w-5 h-5 text-coral" />
              <CardTitle>Appearance</CardTitle>
            </div>
            <CardDescription>Customize the look and feel of your workspace</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Theme</Label>
              <Select value={theme} onValueChange={setTheme}>
                <SelectTrigger className="w-[200px] mt-2" data-testid="select-theme">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Canvas Grid</Label>
              <Select defaultValue="dots">
                <SelectTrigger className="w-[200px] mt-2" data-testid="select-canvas-grid">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dots">Dots</SelectItem>
                  <SelectItem value="lines">Lines</SelectItem>
                  <SelectItem value="none">None</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-coral" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>Manage your account security and API access</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
              <div>
                <h4 className="font-medium">Change Password</h4>
                <p className="text-sm text-gray-500">Update your account password</p>
              </div>
              <Button 
                variant="outline" 
                className="border-2 border-gray-300 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-change-password"
              >
                Change Password
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
              <div>
                <h4 className="font-medium">API Keys</h4>
                <p className="text-sm text-gray-500">Manage API keys for external integrations</p>
              </div>
              <Button 
                variant="outline" 
                className="border-2 border-gray-300 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-manage-api-keys"
              >
                <Key className="w-4 h-4 mr-2" />
                Manage Keys
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
              <div>
                <h4 className="font-medium">Two-Factor Authentication</h4>
                <p className="text-sm text-gray-500">Add an extra layer of security</p>
                <Badge variant="outline" className="mt-1">Not Enabled</Badge>
              </div>
              <Button 
                variant="outline" 
                className="border-2 border-gray-300 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-setup-2fa"
              >
                Setup
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Data Management */}
        <Card className="border-2 border-gray-200 hover:border-coral/30 transition-all duration-200">
          <CardHeader>
            <CardTitle>Data Management</CardTitle>
            <CardDescription>Export, import, or delete your workflow data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
              <div>
                <h4 className="font-medium">Export Workflows</h4>
                <p className="text-sm text-gray-500">Download all your workflows as JSON</p>
              </div>
              <Button 
                variant="outline" 
                className="border-2 border-gray-300 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-export-workflows"
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border border-border-light rounded-lg">
              <div>
                <h4 className="font-medium">Import Workflows</h4>
                <p className="text-sm text-gray-500">Upload workflows from a JSON file</p>
              </div>
              <Button 
                variant="outline" 
                className="border-2 border-gray-300 hover:border-coral hover:bg-coral hover:text-white transition-all duration-200"
                data-testid="button-import-workflows"
              >
                <Upload className="w-4 h-4 mr-2" />
                Import
              </Button>
            </div>
            <div className="flex items-center justify-between p-4 border border-red-200 rounded-lg bg-red-50">
              <div>
                <h4 className="font-medium text-red-700">Delete Account</h4>
                <p className="text-sm text-red-600">Permanently delete your account and all data</p>
              </div>
              <Button 
                variant="destructive" 
                className="transition-all duration-200 transform hover:scale-105"
                data-testid="button-delete-account"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
          </div>
        </div>
      </div>
    </div>
  );
}