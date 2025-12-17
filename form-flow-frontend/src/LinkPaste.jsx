import React, { useState } from 'react'
import axios from 'axios';
import VoiceFormFiller from './VoiceFormFiller';
import FormCompletion from './FormCompletion';
import { TransformationTimeline } from './TransformationTimeline';
import { Hero } from '@/components/ui/animated-hero';

const LinkPaste = () => {
    const [url, setUrl] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [showVoiceForm, setShowVoiceForm] = useState(false);
    const [completedData, setCompletedData] = useState(null);
    const [showCompletion, setShowCompletion] = useState(false);

    const handleSubmit = async(e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await axios.post("http://localhost:8000/scrape", {url: url});
            setResult(response.data);
            setUrl('');
        } catch(error) {
            console.log("Error submitting URL:", error);
            alert("Failed to submit URL. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    const startVoiceFilling = () => {
        setShowVoiceForm(true);
    }

    React.useEffect(() => {
        if (result && !showVoiceForm && !showCompletion) {
            startVoiceFilling();
        }
    }, [result]);

    const handleVoiceComplete = (formData) => {
        setCompletedData(formData);
        setShowVoiceForm(false);
        setShowCompletion(true);
    }

    const handleReset = () => {
        setResult(null);
        setCompletedData(null);
        setShowCompletion(false);
        setShowVoiceForm(false);
        setUrl('');
    }

    if (showCompletion && completedData && result) {
        return (
            <FormCompletion 
                formData={completedData}
                formSchema={result.form_schema}
                originalUrl={url}
                onReset={handleReset}
            />
        );
    }

    if (showVoiceForm && result) {
        return (
            <VoiceFormFiller 
                formSchema={result.form_schema}
                formContext={result.form_context}
                onComplete={handleVoiceComplete}
            />
        );
    }

    return (
        <div>
            {!result && (
                <>
                    <Hero url={url} setUrl={setUrl} handleSubmit={handleSubmit} loading={loading} />
                    <TransformationTimeline />
                </>
            )}
        </div>
    )
}

export default LinkPaste;