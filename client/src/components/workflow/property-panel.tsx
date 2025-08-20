import { useState, useEffect } from "react";
import { X } from "lucide-react";
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
          <div key={key}>
            <Label htmlFor={inputId} className="text-sm font-medium text-gray-700 mb-1">
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </Label>
            <Select 
              value={formData[key] || value} 
              onValueChange={(val) => setFormData({...formData, [key]: val})}
            >
              <SelectTrigger data-testid={`select-${key}`}>
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
          <div key={key}>
            <Label htmlFor={inputId} className="text-sm font-medium text-gray-700 mb-1">
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </Label>
            <Select 
              value={formData[key] || value} 
              onValueChange={(val) => setFormData({...formData, [key]: val})}
            >
              <SelectTrigger data-testid={`select-${key}`}>
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
        <div key={key}>
          <Label htmlFor={inputId} className="text-sm font-medium text-gray-700 mb-1">
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </Label>
          <Input
            id={inputId}
            type="text"
            value={formData[key] || value}
            onChange={(e) => setFormData({...formData, [key]: e.target.value})}
            data-testid={`input-${key}`}
          />
        </div>
      );
    });
  };

  return (
    <div 
      className="fixed right-4 top-1/2 transform -translate-y-1/2 w-80 bg-white rounded-xl shadow-2xl border border-border-light z-30"
      data-testid="property-panel"
    >
      <div className="p-4 border-b border-border-light">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-text-dark">Node Properties</h3>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            data-testid="button-close-properties"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
      
      <div className="p-4 max-h-96 overflow-y-auto">
        <div className="space-y-4">
          <div>
            <Label htmlFor="node-name" className="text-sm font-medium text-gray-700 mb-1">
              Name
            </Label>
            <Input
              id="node-name"
              type="text"
              value={formData.label || ''}
              onChange={(e) => setFormData({...formData, label: e.target.value})}
              data-testid="input-node-name"
            />
          </div>
          
          <div>
            <Label htmlFor="node-description" className="text-sm font-medium text-gray-700 mb-1">
              Description
            </Label>
            <Input
              id="node-description"
              type="text"
              value={formData.description || ''}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              data-testid="input-node-description"
            />
          </div>
          
          {renderConfigFields()}
        </div>
      </div>
      
      <div className="p-4 border-t border-border-light">
        <div className="flex space-x-2">
          <Button 
            className="flex-1 bg-coral hover:bg-red-600 text-white"
            onClick={handleSave}
            data-testid="button-save-properties"
          >
            Save Changes
          </Button>
          <Button 
            variant="outline" 
            onClick={onClose}
            data-testid="button-cancel-properties"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
