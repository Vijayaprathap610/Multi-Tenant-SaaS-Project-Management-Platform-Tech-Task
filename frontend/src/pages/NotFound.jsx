import { Link } from "react-router";
import Logo from "../components/Logo";

export default function NotFound({ inApp = false }) {
  return (
    <div className={inApp ? "text-center py-5" : "tt-auth-wrap align-items-center justify-content-center text-center p-4"}>
      {!inApp && <div className="mb-4"><Logo size={40} /></div>}
      <h1 className="h3">Page not found</h1>
      <p className="text-muted">The page you are looking for does not exist, or you do not have access to it.</p>
      <Link to={inApp ? "/app" : "/"} className="btn btn-primary">Go back</Link>
    </div>
  );
}
