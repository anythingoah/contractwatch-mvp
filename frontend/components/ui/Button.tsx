type ButtonOptions = {
  variant?: "primary" | "outline";
  size?: "sm" | "md";
  className?: string;
};

export function buttonVariants({ variant = "primary", size = "md", className = "" }: ButtonOptions = {}) {
  const base = "inline-flex items-center justify-center rounded-full font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
  const variants = variant === "primary"
    ? "bg-ink text-bg hover:bg-white"
    : "border border-border text-ink hover:bg-white/5";
  const sizes = size === "sm" ? "px-3 py-1.5 text-sm" : "px-4 py-2 text-sm";
  return `${base} ${variants} ${sizes} ${className}`.trim();
}
