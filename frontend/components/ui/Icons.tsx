import type { SVGProps } from "react";

export function CheckCircleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path d="M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="m5.25 8 1.8 1.8 3.7-3.7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
