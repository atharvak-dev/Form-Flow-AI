import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Play, Pause, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import Aurora from '@/components/ui/Aurora';

const VoiceFormFiller = ({ formSchema, formContext, onComplete }) => {
  const [isListening, setIsListening] = useState(false);
  const [currentFieldIndex, setCurrentFieldIndex] = useState(0);
  const [formData, setFormData] = useState({});
  const [transcript, setTranscript] = useState('');
  const [processing, setProcessing] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [pauseTimer, setPauseTimer] = useState(null);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [useDeepgram, setUseDeepgram] = useState(true); // Try Deepgram first

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null); // Fallback for browser STT
  const pauseTimeoutRef = useRef(null);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

  const allFields = formSchema.flatMap(form =>
    form.fields.filter(field => !field.hidden && field.type !== 'submit')
  );

  useEffect(() => {
    // Initialize browser fallback STT
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = handleBrowserSpeechResult;
      recognitionRef.current.onend = handleBrowserSpeechEnd;
      recognitionRef.current.onerror = handleBrowserSpeechError;
    }

    if (allFields.length > 0) {
      setCurrentPrompt(allFields[0].smart_prompt || `Please provide ${allFields[0].label || allFields[0].name}`);
      playFieldSpeech(allFields[0]);
    }

    return () => {
      // Cleanup
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Browser fallback handlers (used when Deepgram fails)
  const handleBrowserSpeechResult = (event) => {
    let finalTranscript = '';
    let interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }

    setTranscript(finalTranscript || interimTranscript);

    if (finalTranscript) {
      clearTimeout(pauseTimeoutRef.current);
      processVoiceInput(finalTranscript);
    } else {
      clearTimeout(pauseTimeoutRef.current);
      pauseTimeoutRef.current = setTimeout(() => {
        handleUserPause();
      }, 3000);
    }
  };

  const handleBrowserSpeechEnd = () => {
    if (isListening && !useDeepgram) {
      recognitionRef.current.start();
    }
  };

  const handleBrowserSpeechError = (event) => {
    console.error('Browser speech recognition error:', event.error);
    if (event.error === 'not-allowed') {
      alert('Microphone access denied. Please allow microphone access in your browser settings.');
    } else if (event.error === 'no-speech') {
      console.log('No speech detected, continuing to listen...');
      return;
    }
    setIsListening(false);
  };

  // Deepgram-based recording
  const startListening = async () => {
    setTranscript('');
    setSuggestions([]);

    if (useDeepgram) {
      try {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        // Create MediaRecorder
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm;codecs=opus'
        });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          // Send recorded audio to Deepgram
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          await transcribeWithDeepgram(audioBlob);
        };

        mediaRecorder.start();
        setIsListening(true);
        setIsRecording(true);
        console.log('🎤 Started Deepgram recording');

      } catch (error) {
        console.error('Failed to start Deepgram recording:', error);
        // Fall back to browser STT
        setUseDeepgram(false);
        startBrowserListening();
      }
    } else {
      startBrowserListening();
    }
  };

  const startBrowserListening = () => {
    if (recognitionRef.current) {
      try {
        setIsListening(true);
        setTranscript('');
        recognitionRef.current.start();
      } catch (error) {
        console.error('Error starting browser speech recognition:', error);
        alert('Failed to start voice input. Please try again.');
        setIsListening(false);
      }
    } else {
      alert('Voice input is not available. Please check your browser compatibility.');
    }
  };

  const stopListening = async () => {
    setIsListening(false);
    clearTimeout(pauseTimeoutRef.current);

    if (useDeepgram && mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  };

  const transcribeWithDeepgram = async (audioBlob) => {
    setProcessing(true);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await axios.post('http://localhost:8000/transcribe', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success && response.data.transcript) {
        const transcribedText = response.data.transcript;
        console.log('✅ Deepgram transcript:', transcribedText);
        setTranscript(transcribedText);
        await processVoiceInput(transcribedText);
      } else if (response.data.use_browser_fallback) {
        console.log('⚠️ Deepgram not available, using browser fallback');
        setUseDeepgram(false);
        setSuggestions(['Deepgram unavailable. Using browser voice recognition instead.']);
        setProcessing(false);
      } else {
        setSuggestions(['Could not transcribe audio. Please try again.']);
        setProcessing(false);
      }
    } catch (error) {
      console.error('Deepgram transcription error:', error);
      setSuggestions(['Transcription failed. Please try again.']);
      setProcessing(false);
    }
  };

  const processVoiceInput = async (voiceText) => {
    if (currentFieldIndex >= allFields.length) return;

    setProcessing(true);
    const currentField = allFields[currentFieldIndex];

    try {
      const response = await axios.post('http://localhost:8000/process-voice', {
        transcript: voiceText,
        field_info: currentField,
        form_context: formContext
      });

      const { processed_text, confidence, pronunciation_check, clarifying_questions } = response.data;

      if (confidence < 0.6 || pronunciation_check.needs_confirmation) {
        setNeedsConfirmation(true);
        setSuggestions([
          `I heard: "${processed_text}". Is this correct?`,
          ...(clarifying_questions || [])
        ]);
      } else {
        confirmFieldValue(processed_text);
      }
    } catch (error) {
      console.error('Voice processing error:', error);
      setSuggestions(['Sorry, I had trouble processing that. Could you try again?']);
    } finally {
      setProcessing(false);
    }
  };

  const confirmFieldValue = (value) => {
    const currentField = allFields[currentFieldIndex];

    // Store password value for confirm password auto-fill
    const fieldName = (currentField.name || '').toLowerCase();
    const fieldLabel = (currentField.label || '').toLowerCase();
    const isPasswordField = currentField.type === 'password' ||
      fieldName.includes('password') ||
      fieldLabel.includes('password');

    // Store password if this is a password field (but not confirm password)
    if (isPasswordField && !fieldName.includes('confirm') && !fieldLabel.includes('confirm')) {
      window._lastPasswordValue = value;
    }

    setFormData(prev => ({
      ...prev,
      [currentField.name]: value
    }));

    moveToNextField();
  };

  const moveToNextField = () => {
    const nextIndex = currentFieldIndex + 1;
    if (nextIndex < allFields.length) {
      const nextField = allFields[nextIndex];
      const nextFieldName = (nextField.name || '').toLowerCase();
      const nextFieldLabel = (nextField.label || '').toLowerCase();

      // Check if next field is confirm password and we have a stored password
      const isConfirmPassword =
        (nextField.type === 'password' || nextFieldName.includes('password') || nextFieldLabel.includes('password')) &&
        (nextFieldName.includes('confirm') || nextFieldLabel.includes('confirm') ||
          nextFieldName.includes('repeat') || nextFieldLabel.includes('repeat') ||
          nextFieldName.includes('retype') || nextFieldLabel.includes('retype'));

      if (isConfirmPassword && window._lastPasswordValue) {
        // Auto-fill confirm password with the stored password value
        console.log('🔒 Auto-filling confirm password');
        setFormData(prev => ({
          ...prev,
          [nextField.name]: window._lastPasswordValue
        }));

        // Skip to the field after confirm password
        setCurrentFieldIndex(nextIndex + 1);
        if (nextIndex + 1 < allFields.length) {
          setCurrentPrompt(allFields[nextIndex + 1].smart_prompt || `Please provide ${allFields[nextIndex + 1].label || allFields[nextIndex + 1].name}`);
          playFieldSpeech(allFields[nextIndex + 1]);
        } else {
          // Form complete
          stopListening();
          // Include the auto-filled confirm password in final data
          const finalData = { ...formData, [nextField.name]: window._lastPasswordValue };
          onComplete(finalData);
        }
        return;
      }

      setCurrentFieldIndex(nextIndex);
      setCurrentPrompt(allFields[nextIndex].smart_prompt || `Please provide ${allFields[nextIndex].label || allFields[nextIndex].name}`);
      setTranscript('');
      setNeedsConfirmation(false);
      setSuggestions([]);
      playFieldSpeech(allFields[nextIndex]);
    } else {
      // Form complete
      stopListening();
      onComplete(formData);
    }
  };

  const playFieldSpeech = async (field) => {
    try {
      setIsPlayingAudio(true);
      const response = await fetch(`http://localhost:8000/speech/${field.name}`);
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          audioRef.current.play();
        }
      }
    } catch (error) {
      console.error('Error playing field speech:', error);
    } finally {
      setIsPlayingAudio(false);
    }
  };

  const handleAudioEnded = () => {
    setIsPlayingAudio(false);
  };

  const handleUserPause = async () => {
    if (currentFieldIndex >= allFields.length) return;

    try {
      const response = await axios.post('http://localhost:8000/pause-suggestions', {
        field_info: allFields[currentFieldIndex],
        form_context: formContext
      });
      setSuggestions(response.data.suggestions);
    } catch (error) {
      setSuggestions(['Take your time. You can continue when ready.']);
    }
  };

  const handleConfirmation = (confirmed) => {
    if (confirmed) {
      confirmFieldValue(transcript);
    } else {
      setNeedsConfirmation(false);
      setSuggestions(['Please try again.']);
      setTranscript('');
    }
  };

  const currentField = allFields[currentFieldIndex];
  const progress = ((currentFieldIndex + 1) / allFields.length) * 100;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <Aurora colorStops={['#bfe4be', '#69da93', '#86efac']} amplitude={1.0} blend={0.5} speed={0.4} />
      <div className="max-w-2xl w-full p-6 bg-card/95 backdrop-blur-sm rounded-2xl shadow-2xl border border-border relative z-10">
        <div className="mb-8">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">Voice Form Filling</h2>
            <span className="text-base text-muted-foreground font-medium">
              {currentFieldIndex + 1} of {allFields.length}
            </span>
          </div>
          <div className="w-full bg-muted rounded-full h-3">
            <div
              className="bg-primary h-3 rounded-full transition-all duration-300 shadow-lg"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {currentField && (
          <div className="mb-6">
            <div className="bg-muted/50 p-6 rounded-xl mb-4 border border-border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xl font-semibold text-foreground">{currentPrompt}</p>
                  {currentField.required && (
                    <p className="text-sm text-muted-foreground mt-2 font-medium">* This field is required</p>
                  )}
                </div>
                <button
                  onClick={() => playFieldSpeech(currentField)}
                  className="p-2 text-primary hover:bg-accent rounded-full"
                  disabled={isPlayingAudio}
                >
                  {isPlayingAudio ? <Pause size={20} /> : <Play size={20} />}
                </button>
              </div>
              <audio
                ref={audioRef}
                onEnded={handleAudioEnded}
                style={{ display: 'none' }}
              />
            </div>

            {/* Dropdown/Select Options Chips */}
            {(currentField.is_dropdown || currentField.type === 'select' || currentField.type === 'dropdown' || currentField.type === 'radio') && currentField.options && currentField.options.length > 0 && (
              <div className="bg-muted/50 p-4 rounded-xl mb-4 border border-border">
                <p className="text-sm font-medium text-muted-foreground mb-3">
                  Tap to select or speak your choice:
                </p>
                <div className="flex flex-wrap gap-2">
                  {currentField.options.map((option, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        const value = option.value || option.label;
                        confirmFieldValue(value);
                      }}
                      disabled={option.disabled || processing}
                      className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 border
                      ${option.disabled
                          ? 'bg-muted text-muted-foreground cursor-not-allowed opacity-50'
                          : 'bg-background hover:bg-primary hover:text-primary-foreground border-border hover:border-primary shadow-sm hover:shadow-md'
                        }
                    `}
                    >
                      {option.label || option.value}
                      {option.selected && <span className="ml-1 text-primary">✓</span>}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-3 italic">
                  Or use the microphone below to speak your choice
                </p>
              </div>
            )}

            <div className="flex items-center justify-center mb-6">
              <button
                onClick={isListening ? stopListening : startListening}
                className={`p-6 rounded-full shadow-2xl ${isListening
                  ? 'bg-destructive hover:bg-destructive/90 text-destructive-foreground'
                  : 'bg-primary hover:bg-primary/90 text-primary-foreground'
                  } transition-all duration-200 hover:scale-110`}
                disabled={processing}
              >
                {isListening ? <MicOff size={32} /> : <Mic size={32} />}
              </button>
            </div>

            {transcript && (
              <div className="bg-muted/50 p-4 rounded-xl mb-4 border border-border">
                <p className="text-sm text-muted-foreground font-medium mb-1">You said:</p>
                <p className="text-lg font-semibold text-foreground">{transcript}</p>
              </div>
            )}

            {processing && (
              <div className="text-center text-primary mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                <p className="mt-3 text-foreground font-medium text-lg">Processing your response...</p>
              </div>
            )}

            {needsConfirmation && (
              <div className="bg-muted/50 p-6 rounded-xl mb-4 border border-border">
                <div className="flex items-center mb-4">
                  <AlertCircle className="text-accent mr-2" size={24} />
                  <p className="font-semibold text-foreground text-lg">Please confirm</p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleConfirmation(true)}
                    className="flex-1 px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 font-semibold transition-all shadow-lg"
                  >
                    Yes, correct
                  </button>
                  <button
                    onClick={() => handleConfirmation(false)}
                    className="flex-1 px-6 py-3 bg-destructive text-destructive-foreground rounded-xl hover:bg-destructive/90 font-semibold transition-all shadow-lg"
                  >
                    No, try again
                  </button>
                </div>
              </div>
            )}

            {suggestions.length > 0 && !needsConfirmation && (
              <div className="bg-muted/50 p-6 rounded-xl border border-border">
                <p className="font-semibold text-foreground mb-3 text-lg">Helpful suggestions:</p>
                <ul className="text-sm text-muted-foreground space-y-2">
                  {suggestions.map((suggestion, index) => (
                    <li key={index} className="leading-relaxed">• {suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {Object.keys(formData).length > 0 && (
          <div className="mt-6 p-6 bg-muted/50 rounded-xl border border-border">
            <h3 className="font-semibold mb-3 text-foreground text-lg">Collected Information:</h3>
            <div className="space-y-1 text-sm">
              {Object.entries(formData).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground">{key}:</span>
                  <span className="font-medium text-foreground">{value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceFormFiller;