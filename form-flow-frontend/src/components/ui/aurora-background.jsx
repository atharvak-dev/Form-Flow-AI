import React from "react";
import { cn } from "@/lib/utils";

export const AuroraBackground = ({ className, children, showRadialGradient = true, ...props }) => {
  return (
    <div className={cn("relative flex flex-col", className)} {...props}>
      <div className="absolute inset-0 overflow-hidden">
        <div
          className={cn(
            `
            [--green-500:rgba(34,197,94,0.5)]
            [--green-300:rgba(134,239,172,0.5)]
            [--green-600:rgba(22,163,74,0.4)]
            [--green-400:rgba(74,222,128,0.5)]
            [--green-700:rgba(21,128,61,0.4)]
            after:content-[""] after:absolute after:inset-0 after:[background-image:radial-gradient(ellipse_80%_80%_at_50%_-20%,var(--green-500),rgba(255,255,255,0))]
            after:animate-aurora
            [background-image:repeating-linear-gradient(100deg,var(--green-400)_0%,var(--green-300)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--green-300)_16%),repeating-linear-gradient(100deg,var(--green-600)_0%,var(--green-500)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--green-500)_16%),repeating-linear-gradient(100deg,var(--green-700)_0%,var(--green-600)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--green-600)_16%),repeating-linear-gradient(100deg,var(--green-500)_0%,var(--green-400)_7%,var(--transparent)_10%,var(--transparent)_12%,var(--green-400)_16%)]
            [background-size:300%,_200%,_100%,_80%]
            [background-position:0%_0%,_50%_50%,_50%_50%,_50%_50%]
            filter blur-[10px] invert-0
            after:inset-[10px] after:content-[""] after:rounded-[inherit] after:[background:linear-gradient(to_bottom,var(--green-500),var(--green-600)_30%,var(--green-700))]
            absolute -inset-[10px] opacity-50 will-change-transform`,
            showRadialGradient &&
              `[mask-image:radial-gradient(ellipse_at_100%_0%,black_10%,var(--transparent)_70%)]`
          )}
        ></div>
      </div>
      {children}
    </div>
  );
};
