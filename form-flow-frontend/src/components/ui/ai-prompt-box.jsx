import React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { ArrowUp, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";

const Textarea = React.forwardRef(({ className, ...props }, ref) => (
  <textarea
    className={cn(
      "flex w-full rounded-md border-none bg-transparent px-3 py-2.5 text-base text-gray-100 placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50 min-h-[44px] resize-none",
      className
    )}
    ref={ref}
    rows={1}
    {...props}
  />
));
Textarea.displayName = "Textarea";

const TooltipProvider = TooltipPrimitive.Provider;
const Tooltip = TooltipPrimitive.Root;
const TooltipTrigger = TooltipPrimitive.Trigger;
const TooltipContent = React.forwardRef(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      "z-50 overflow-hidden rounded-md border border-[#333333] bg-[#1F2023] px-3 py-1.5 text-sm text-white shadow-md",
      className
    )}
    {...props}
  />
));
TooltipContent.displayName = TooltipPrimitive.Content.displayName;

const PromptInputContext = React.createContext({
  isLoading: false,
  value: "",
  setValue: () => {},
  maxHeight: 240,
  onSubmit: undefined,
  disabled: false,
});

function usePromptInput() {
  const context = React.useContext(PromptInputContext);
  if (!context) throw new Error("usePromptInput must be used within a PromptInput");
  return context;
}

const PromptInput = React.forwardRef(
  ({ className, isLoading = false, maxHeight = 240, value, onValueChange, onSubmit, children, disabled = false }, ref) => {
    const [internalValue, setInternalValue] = React.useState(value || "");
    const handleChange = (newValue) => {
      setInternalValue(newValue);
      onValueChange?.(newValue);
    };
    return (
      <TooltipProvider>
        <PromptInputContext.Provider
          value={{
            isLoading,
            value: value ?? internalValue,
            setValue: onValueChange ?? handleChange,
            maxHeight,
            onSubmit,
            disabled,
          }}
        >
          <div
            ref={ref}
            className={cn(
              "rounded-3xl border border-[#444444] bg-[#1F2023] p-2 shadow-[0_8px_30px_rgba(0,0,0,0.24)] transition-all duration-300",
              isLoading && "border-primary/70",
              className
            )}
          >
            {children}
          </div>
        </PromptInputContext.Provider>
      </TooltipProvider>
    );
  }
);
PromptInput.displayName = "PromptInput";

const PromptInputTextarea = ({ className, onKeyDown, disableAutosize = false, placeholder, ...props }) => {
  const { value, setValue, maxHeight, onSubmit, disabled } = usePromptInput();
  const textareaRef = React.useRef(null);

  React.useEffect(() => {
    if (disableAutosize || !textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height =
      typeof maxHeight === "number"
        ? `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`
        : `min(${textareaRef.current.scrollHeight}px, ${maxHeight})`;
  }, [value, maxHeight, disableAutosize]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit?.();
    }
    onKeyDown?.(e);
  };

  return (
    <Textarea
      ref={textareaRef}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onKeyDown={handleKeyDown}
      className={cn("text-base", className)}
      disabled={disabled}
      placeholder={placeholder}
      {...props}
    />
  );
};

const PromptInputActions = ({ children, className, ...props }) => (
  <div className={cn("flex items-center gap-2", className)} {...props}>
    {children}
  </div>
);

const PromptInputAction = ({ tooltip, children, className, side = "top", ...props }) => {
  const { disabled } = usePromptInput();
  return (
    <Tooltip {...props}>
      <TooltipTrigger asChild disabled={disabled}>
        {children}
      </TooltipTrigger>
      <TooltipContent side={side} className={className}>
        {tooltip}
      </TooltipContent>
    </Tooltip>
  );
};

const Button = React.forwardRef(({ className, variant = "default", size = "default", ...props }, ref) => {
  const variantClasses = {
    default: "bg-white hover:bg-white/80 text-black",
    outline: "border border-[#444444] bg-transparent hover:bg-[#3A3A40]",
    ghost: "bg-transparent hover:bg-[#3A3A40]",
  };
  const sizeClasses = {
    default: "h-10 px-4 py-2",
    sm: "h-8 px-3 text-sm",
    lg: "h-12 px-6",
    icon: "h-8 w-8 rounded-full aspect-[1/1]",
  };
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Button.displayName = "Button";

export const PromptInputBox = React.forwardRef((props, ref) => {
  const { onSend = () => {}, isLoading = false, placeholder = "Paste form URL here...", className } = props;
  const [input, setInput] = React.useState("");
  const uploadInputRef = React.useRef(null);

  const handleSubmit = () => {
    if (input.trim()) {
      onSend(input);
      setInput("");
    }
  };

  const hasContent = input.trim() !== "";

  return (
    <PromptInput
      value={input}
      onValueChange={setInput}
      isLoading={isLoading}
      onSubmit={handleSubmit}
      className={cn("w-full bg-[#1F2023] border-[#444444]", className)}
      disabled={isLoading}
      ref={ref}
    >
      <PromptInputTextarea placeholder={placeholder} className="text-base" />

      <PromptInputActions className="flex items-center justify-between gap-2 p-0 pt-2">
        <div className="flex items-center gap-1">
          <PromptInputAction tooltip="Upload image">
            <button
              onClick={() => uploadInputRef.current?.click()}
              className="flex h-8 w-8 text-[#9CA3AF] cursor-pointer items-center justify-center rounded-full transition-colors hover:bg-gray-600/30 hover:text-[#D1D5DB]"
            >
              <Paperclip className="h-5 w-5 transition-colors" />
              <input
                ref={uploadInputRef}
                type="file"
                className="hidden"
                accept="image/*"
              />
            </button>
          </PromptInputAction>
        </div>

        <PromptInputAction tooltip={isLoading ? "Analyzing..." : hasContent ? "Analyze form" : "Enter URL"}>
          <Button
            variant="default"
            size="icon"
            className={cn(
              "h-8 w-8 rounded-full transition-all duration-200",
              hasContent
                ? "bg-white hover:bg-white/80 text-[#1F2023]"
                : "bg-transparent hover:bg-gray-600/30 text-[#9CA3AF] hover:text-[#D1D5DB]"
            )}
            onClick={handleSubmit}
            disabled={isLoading || !hasContent}
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </PromptInputAction>
      </PromptInputActions>
    </PromptInput>
  );
});
PromptInputBox.displayName = "PromptInputBox";
