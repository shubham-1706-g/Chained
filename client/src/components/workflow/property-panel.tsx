import { useState, useEffect } from "react";
import { X, Save, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { WorkflowNode } from "@shared/schema";

interface PropertyPanelProps {
  node: WorkflowNode | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (nodeId: string, data: any) => void;
}

export function PropertyPanel({ node, isOpen, onClose, onSave }: PropertyPanelProps) {
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    if (node) {
      setFormData({
        label: node.data.label,
        description: node.data.description || '',
        ...node.data.config
      });
    }
  }, [node]);

  if (!isOpen || !node) return null;

  const handleSave = () => {
    const { label, description, ...config } = formData;
    onSave(node.id, {
      label,
      description,
      config
    });
    onClose();
  };

  const renderConfigFields = () => {
    if (!node.data.config) return null;

    return Object.entries(node.data.config).map(([key, value]) => {
      const inputId = `config-${key}`;
      
      if (key === 'method' && typeof value === 'string') {
        return (
          <div key={key} className="space-y-2">
            <Label htmlFor={inputId} className="text-gray-900 mb-2 block">
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </Label>
            <Select 
              value={formData[key] || value} 
              onValueChange={(val) => setFormData({...formData, [key]: val})}
            >
              <SelectTrigger data-testid={`select-${key}`} className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GET">GET</SelectItem>
                <SelectItem value="POST">POST</SelectItem>
                <SelectItem value="PUT">PUT</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
              </SelectContent>
            </Select>
          </div>
        );
      }

      if (key === 'operation' && typeof value === 'string') {
        return (
          <div key={key} className="space-y-2">
            <Label htmlFor={inputId} className="text-gray-900 mb-2 block">
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </Label>
            <Select 
              value={formData[key] || value} 
              onValueChange={(val) => setFormData({...formData, [key]: val})}
            >
              <SelectTrigger data-testid={`select-${key}`} className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="SELECT">SELECT</SelectItem>
                <SelectItem value="INSERT">INSERT</SelectItem>
                <SelectItem value="UPDATE">UPDATE</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
              </SelectContent>
            </Select>
          </div>
        );
      }

      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={inputId} className="text-gray-900 mb-2 block">
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </Label>
          <Input
            id={inputId}
            type="text"
            value={formData[key] || value}
            onChange={(e) => setFormData({...formData, [key]: e.target.value})}
            data-testid={`input-${key}`}
            className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none"
          />
        </div>
      );
    });
  };

  return (
    <div 
      className="fixed right-6 top-1/2 transform -translate-y-1/2 w-96 bg-white rounded-xl shadow-xl border-2 border-gray-200 z-30 ring-1 ring-black/5"
      data-testid="property-panel"
    >
      <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white rounded-t-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-coral rounded-lg flex items-center justify-center">
              <Settings className="w-4 h-4 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Node Properties</h3>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            data-testid="button-close-properties"
            className="h-8 w-8 rounded-full hover:bg-gray-100"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      <div className="p-6 max-h-96 overflow-y-auto">
        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="node-name" className="text-gray-900 mb-2 block">
              Name
            </Label>
            <Input
              id="node-name"
              type="text"
              value={formData.label || ''}
              onChange={(e) => setFormData({...formData, label: e.target.value})}
              data-testid="input-node-name"
              placeholder="Enter node name"
              className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="node-description" className="text-gray-900 mb-2 block">
              Description
            </Label>
            <Textarea
              id="node-description"
              value={formData.description || ''}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              data-testid="input-node-description"
              placeholder="Enter description (optional)"
              className="border border-gray-200 hover:border-gray-300 focus:border-coral-400 focus:ring-2 focus:ring-coral-100 focus:outline-none resize-none"
            />
          </div>
          
          {renderConfigFields()}
        </div>
      </div>
      
      <div className="p-6 border-t border-gray-100 bg-gradient-to-r from-gray-50 to-white rounded-b-xl">
        <div className="flex space-x-3">
          <Button 
            className="flex-1 bg-coral hover:bg-red-600 text-white border-2 border-coral hover:border-red-500 transition-all duration-200"
            onClick={handleSave}
            data-testid="button-save-properties"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
          <Button 
            variant="outline" 
            onClick={onClose}
            data-testid="button-cancel-properties"
            className="border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
