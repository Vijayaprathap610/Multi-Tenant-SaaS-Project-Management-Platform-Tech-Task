import { useState } from "react";
import { Alert, Button, Card, Form } from "react-bootstrap";
import { api, errorMessage, fieldErrors } from "../api/client";
import { PasswordInput } from "../components/common";
import { useAuth } from "../context/AuthContext";

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [name, setName] = useState(user.first_name || "");
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [msg, setMsg] = useState({});
  const [errors, setErrors] = useState({});

  const saveName = async (e) => {
    e.preventDefault();
    try { await api.patch("/auth/me/", { first_name: name }); await refresh(); setMsg({ profile: "Profile saved." }); }
    catch (err) { setMsg({ profileErr: errorMessage(err) }); }
  };
  const changePw = async (e) => {
    e.preventDefault();
    setErrors({}); setMsg({});
    try { await api.post("/auth/change-password/", pw); setPw({ current_password: "", new_password: "" }); setMsg({ pw: "Password changed. Other devices were signed out." }); }
    catch (err) { setErrors(fieldErrors(err)); setMsg({ pwErr: errorMessage(err) }); }
  };

  return (
    <>
      <h1 className="h4 mb-3">Profile</h1>
      <Card className="mb-3"><Card.Body>
        {msg.profile && <Alert variant="success">{msg.profile}</Alert>}
        {msg.profileErr && <Alert variant="danger" role="alert">{msg.profileErr}</Alert>}
        <Form onSubmit={saveName}>
          <Form.Group className="mb-3" controlId="email"><Form.Label>Email</Form.Label><Form.Control value={user.email} disabled readOnly /></Form.Group>
          <Form.Group className="mb-3" controlId="name"><Form.Label>Name</Form.Label>
            <Form.Control value={name} onChange={(e) => setName(e.target.value)} maxLength={150} /></Form.Group>
          <Button type="submit">Save</Button>
        </Form>
      </Card.Body></Card>
      <Card><Card.Body>
        <h2 className="h6">Change password</h2>
        {msg.pw && <Alert variant="success">{msg.pw}</Alert>}
        {msg.pwErr && <Alert variant="danger" role="alert">{msg.pwErr}</Alert>}
        <Form onSubmit={changePw}>
          <PasswordInput id="current" label="Current password" value={pw.current_password} autoComplete="current-password"
            error={errors.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} />
          <PasswordInput id="new" label="New password" value={pw.new_password} autoComplete="new-password"
            error={errors.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} />
          <Button type="submit">Change password</Button>
        </Form>
      </Card.Body></Card>
    </>
  );
}
