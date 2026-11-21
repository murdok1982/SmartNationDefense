import clsx from "clsx";

/** Bloque de carga con la misma métrica que el contenido final (evita saltos). */
export default function Skeleton({
  className,
  lines = 1,
}: {
  className?: string;
  lines?: number;
}) {
  if (lines <= 1) return <div className={clsx("skeleton h-3 w-full", className)} aria-hidden="true" />;
  return (
    <div className="space-y-2" aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={clsx("skeleton h-3", className)}
          style={{ width: i === lines - 1 ? "62%" : "100%" }}
        />
      ))}
    </div>
  );
}
