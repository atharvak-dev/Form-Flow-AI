import React, { useState } from 'react';
import { CheckCircle, Send, AlertTriangle, ExternalLink, Download } from 'lucide-react';
import axios from 'axios';
import Aurora from '@/components/ui/Aurora';

const FormCompletion = ({ formData, formSchema, originalUrl, onReset }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const handleSubmitToWebsite = async () => {
    setIsSubmitting(true);
    try {
      const response = await axios.post('http://localhost:8000/submit-form', {
        url: originalUrl,
        form_data: formData,
        form_schema: formSchema
      });

      setSubmissionResult(response.data);
    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionResult({
        success: false,
        message: 'Failed to submit form',
        error: error.response?.data?.detail || error.message
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const downloadFormData = () => {
    const dataStr = JSON.stringify(formData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'form-data.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    const formText = Object.entries(formData)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
    navigator.clipboard.writeText(formText);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <Aurora colorStops={['#1a8917', '#22c55e', '#86efac']} amplitude={1.0} blend={0.5} speed={0.4} />
      <div className="max-w-2xl w-full p-6 bg-card/95 backdrop-blur-sm rounded-2xl shadow-2xl border border-border relative z-10">
      <div className="text-center mb-8">
        <CheckCircle className="mx-auto text-primary mb-6" size={64} />
        <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-4 tracking-tight">Form Completed!</h2>
        <p className="text-lg text-muted-foreground font-medium">
          All required information has been collected successfully.
        </p>
      </div>

      {/* Form Data Summary */}
      <div className="bg-muted/50 p-6 rounded-xl mb-6 border border-border">
        <h3 className="text-xl font-semibold text-foreground mb-4">Collected Information:</h3>
        <div className="space-y-2">
          {Object.entries(formData).map(([key, value]) => (
            <div key={key} className="flex justify-between items-center py-2 border-b border-border last:border-b-0">
              <span className="text-muted-foreground capitalize">{key.replace(/[_-]/g, ' ')}:</span>
              <span className="font-medium text-foreground text-right max-w-xs truncate">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-4">
        {!submissionResult && (
          <>
            <button
              onClick={handleSubmitToWebsite}
              disabled={isSubmitting}
              className="w-full bg-primary hover:bg-primary/90 disabled:bg-primary/50 text-primary-foreground font-semibold py-4 px-6 rounded-xl flex items-center justify-center space-x-2 transition-all shadow-lg hover:shadow-xl text-lg"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-foreground"></div>
                  <span>Submitting to Website...</span>
                </>
              ) : (
                <>
                  <Send size={20} />
                  <span>Submit to Original Website</span>
                </>
              )}
            </button>

            <div className="flex space-x-3">
              <button
                onClick={downloadFormData}
                className="flex-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-medium py-3 px-4 rounded-xl flex items-center justify-center space-x-2 transition-all"
              >
                <Download size={20} />
                <span>Download</span>
              </button>
              
              <button
                onClick={copyToClipboard}
                className="flex-1 bg-secondary hover:bg-secondary/80 text-secondary-foreground font-medium py-3 px-4 rounded-xl flex items-center justify-center space-x-2 transition-all"
              >
                <span>Copy</span>
              </button>
            </div>
          </>
        )}

        {/* Submission Result */}
        {submissionResult && (
          <div className={`p-4 rounded-lg border ${
            submissionResult.success 
              ? 'bg-muted border-primary/20' 
              : 'bg-muted border-destructive/20'
          }`}>
            <div className="flex items-center mb-2">
              {submissionResult.success ? (
                <CheckCircle className="text-primary mr-2" size={20} />
              ) : (
                <AlertTriangle className="text-destructive mr-2" size={20} />
              )}
              <h4 className={`font-semibold ${
                submissionResult.success ? 'text-foreground' : 'text-destructive'
              }`}>
                {submissionResult.success ? 'Submission Successful!' : 'Submission Failed'}
              </h4>
            </div>
            
            <p className={`mb-3 ${
              submissionResult.success ? 'text-foreground' : 'text-destructive'
            }`}>
              {submissionResult.message}
            </p>

            {submissionResult.details && (
              <div className="mb-3">
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-sm text-primary hover:text-primary/80 underline"
                >
                  {showDetails ? 'Hide Details' : 'Show Details'}
                </button>
                
                {showDetails && (
                  <div className="mt-2 p-3 bg-background rounded border border-border text-sm">
                    <pre className="whitespace-pre-wrap text-foreground">
                      {JSON.stringify(submissionResult.details, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {submissionResult.success && (
              <div className="flex items-center space-x-2 text-sm text-foreground">
                <ExternalLink size={16} />
                <span>Your form has been submitted to the original website</span>
              </div>
            )}
          </div>
        )}

        {/* Reset Button */}
        <button
          onClick={onReset}
          className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground font-medium py-3 px-4 rounded-xl transition-all"
        >
          Start New Form
        </button>
      </div>

      {/* Additional Information */}
      <div className="mt-6 p-6 bg-muted/50 rounded-xl border border-border">
        <h4 className="text-lg font-semibold text-foreground mb-3">What happens next?</h4>
        <ul className="text-sm text-muted-foreground space-y-2">
          <li>• Your form data is automatically filled into the original website</li>
          <li>• The form is submitted using secure browser automation</li>
          <li>• You'll receive confirmation of successful submission</li>
          <li>• No personal data is stored on our servers</li>
        </ul>
      </div>
      </div>
    </div>
  );
};

export default FormCompletion;