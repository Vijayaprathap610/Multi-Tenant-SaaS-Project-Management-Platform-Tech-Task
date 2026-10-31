import { Link } from "react-router";

export function LogoMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" role="img" aria-label="Tech Task logo">
      <rect width="32" height="32" rx="7" fill="#4B2E1E" />
      <rect x="6" y="6" width="7" height="14" rx="1.5" fill="#F6F3EF" />
      <rect x="15" y="6" width="7" height="9" rx="1.5" fill="#B8906B" />
      <rect x="15" y="17" width="11" height="9" rx="1.5" fill="#F6F3EF" opacity=".9" />
      <rect x="6" y="22" width="7" height="4" rx="1.5" fill="#7A5236" />
    </svg>
  );
}

export default function Logo({ size = 32, to = "/", wordmark = true }) {
  return (
    <Link to={to} className="d-inline-flex align-items-center gap-2 text-decoration-none" aria-label="Tech Task home">
      <LogoMark size={size} />
      {wordmark && <span className="tt-wordmark" style={{ fontSize: size * 0.7 }}>Tech Task</span>}
    </Link>
  );
}
