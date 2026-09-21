import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, AlertCircle, Loader2 } from 'lucide-react';

export interface SpeechToTextProps {
  value?: string;
  onChange?: (val: string) => void;
  language?: string;
  placeholder?: string;
  className?: string;
  buttonOnly?: boolean;
  onListeningChange?: (isListening: boolean) => void;
  onInterimResult?: (interim: string) => void;
}

// Global reference to prevent multiple recognition instances running simultaneously
let activeRecognitionInstance: any = null;

export const SpeechToText: React.FC<SpeechToTextProps> = ({
  value = '',
  onChange,
  language = 'en-IN',
  placeholder = 'Speak or type here...',
  className = '',
  buttonOnly = false,
  onListeningChange,
  onInterimResult
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [interimTranscript, setInterimTranscript] = useState('');
  
  const recognitionRef = useRef<any>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore cleanup errors
        }
      }
      if (activeRecognitionInstance === recognitionRef.current) {
        activeRecognitionInstance = null;
      }
    };
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore error
      }
    }
    if (isMountedRef.current) {
      setIsListening(false);
      setIsProcessing(false);
      setInterimTranscript('');
      onListeningChange?.(false);
    }
  }, [onListeningChange]);

  const startListening = useCallback(() => {
    setErrorMessage(null);
    setInterimTranscript('');

    // Check browser support
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    // Stop any existing active instance
    if (activeRecognitionInstance && activeRecognitionInstance !== recognitionRef.current) {
      try {
        activeRecognitionInstance.abort();
      } catch {
        // ignore
      }
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      activeRecognitionInstance = recognition;

      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = language || 'en-IN';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        if (!isMountedRef.current) return;
        setIsListening(true);
        setIsProcessing(false);
        onListeningChange?.(true);
      };

      recognition.onresult = (event: any) => {
        if (!isMountedRef.current) return;

        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcriptPiece = event.results[i][0]?.transcript || '';
          if (event.results[i].isFinal) {
            final += transcriptPiece;
          } else {
            interim += transcriptPiece;
          }
        }

        if (interim) {
          setInterimTranscript(interim);
          onInterimResult?.(interim);
        }

        if (final) {
          const trimmedFinal = final.trim();
          const combined = value ? `${value} ${trimmedFinal}` : trimmedFinal;
          onChange?.(combined);
          setInterimTranscript('');
        }
      };

      recognition.onerror = (event: any) => {
        if (!isMountedRef.current) return;

        if (event.error === 'no-speech') {
          setErrorMessage('No speech was detected. Please try again.');
        } else if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          setErrorMessage('Microphone access was denied. Please allow microphone permission in your browser.');
        } else if (event.error === 'network') {
          setErrorMessage('Network error occurred during speech recognition.');
        } else if (event.error !== 'aborted') {
          setErrorMessage(`Speech recognition error: ${event.error}`);
        }

        setIsListening(false);
        setIsProcessing(false);
        onListeningChange?.(false);
      };

      recognition.onend = () => {
        if (!isMountedRef.current) return;
        setIsListening(false);
        setIsProcessing(false);
        onListeningChange?.(false);
        if (activeRecognitionInstance === recognition) {
          activeRecognitionInstance = null;
        }
      };

      recognition.start();
    } catch (err: any) {
      if (!isMountedRef.current) return;
      setErrorMessage(err?.message || 'Could not start speech recognition.');
      setIsListening(false);
      setIsProcessing(false);
      onListeningChange?.(false);
    }
  }, [language, value, onChange, onListeningChange, onInterimResult]);

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const clearError = () => {
    setErrorMessage(null);
  };

  // Button-only mode for embedding directly inside existing input bars
  if (buttonOnly) {
    return (
      <div className={`relative inline-flex items-center ${className}`}>
        <button
          type="button"
          onClick={toggleListening}
          aria-label={isListening ? 'Stop voice recording' : 'Start speech-to-text recording'}
          aria-pressed={isListening}
          className={`relative p-2 rounded-full transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${
            isListening
              ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 scale-105'
              : isProcessing
              ? 'bg-amber-100 text-amber-700'
              : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200'
          }`}
          title={isListening ? 'Listening... Click to stop' : 'Click to speak'}
        >
          {isListening && (
            <span className="absolute inset-0 rounded-full animate-ping bg-red-400 opacity-60 pointer-events-none" />
          )}
          {isProcessing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isListening ? (
            <Mic className="w-4 h-4 animate-pulse" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </button>

        {/* Floating Error Tooltip */}
        {errorMessage && (
          <div className="absolute bottom-full right-0 mb-2 w-64 bg-red-900/90 backdrop-blur-md text-white text-xs rounded-lg p-2.5 shadow-xl border border-red-700 z-50 flex items-start gap-2 animate-in fade-in slide-in-from-bottom-2">
            <AlertCircle className="w-4 h-4 text-red-300 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium leading-tight">{errorMessage}</p>
            </div>
            <button
              type="button"
              onClick={clearError}
              aria-label="Dismiss error"
              className="text-red-300 hover:text-white text-xs font-bold px-1"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    );
  }

  // Full composite component with text input + inline Speech-to-Text mic control
  return (
    <div className={`relative w-full ${className}`}>
      <div className="relative flex items-center">
        <input
          type="text"
          value={interimTranscript ? `${value} [${interimTranscript}]` : value}
          onChange={(e) => onChange?.(e.target.value)}
          placeholder={isListening ? 'Listening to your voice...' : placeholder}
          className={`w-full pr-12 pl-4 py-3 bg-white/90 backdrop-blur-md border rounded-xl text-slate-800 placeholder-slate-400 text-sm shadow-sm transition-all focus:outline-none focus:ring-2 ${
            isListening
              ? 'border-red-400 focus:ring-red-400/30'
              : 'border-slate-200 focus:border-emerald-500 focus:ring-emerald-500/20'
          }`}
        />

        <div className="absolute right-2 flex items-center gap-1.5">
          <button
            type="button"
            onClick={toggleListening}
            aria-label={isListening ? 'Stop voice recording' : 'Start speech-to-text recording'}
            aria-pressed={isListening}
            className={`relative p-2 rounded-lg transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
              isListening
                ? 'bg-red-500 text-white shadow-md shadow-red-500/30'
                : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200'
            }`}
            title={isListening ? 'Listening... Click to stop' : 'Click to speak'}
          >
            {isListening && (
              <span className="absolute inset-0 rounded-lg animate-ping bg-red-400 opacity-50 pointer-events-none" />
            )}
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin text-emerald-700" />
            ) : isListening ? (
              <Mic className="w-4 h-4 animate-pulse text-white" />
            ) : (
              <Mic className="w-4 h-4 text-emerald-700" />
            )}
          </button>
        </div>
      </div>

      {/* Listening status indicator */}
      {isListening && (
        <div className="mt-1.5 flex items-center justify-between text-xs text-red-600 px-1 font-medium animate-pulse">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            Listening in {language}... Speak clearly.
          </span>
          <button
            type="button"
            onClick={stopListening}
            className="text-xs text-slate-500 hover:text-red-700 underline"
          >
            Done speaking
          </button>
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="mt-2 flex items-center justify-between bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg p-2.5">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={clearError}
            className="text-red-500 hover:text-red-800 font-bold px-1"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};

export default SpeechToText;
