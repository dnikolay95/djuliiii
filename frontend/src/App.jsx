import { useEffect, useMemo, useState } from "react";
import "./style.css";

const API_BASE = "http://localhost:8011";
const WS_BASE = "ws://localhost:8011/ws";

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

const tabs = [
  { id: "users", title: "Users" },
  { id: "greetings", title: "Greetings" },
  { id: "messages", title: "Messages" },
];

function LoginForm({ onLogin }) {
  const [login, setLogin] = useState("admin");
  const [password, setPassword] = useState("admin2");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ login, password }),
      });
      await onLogin();
    } catch (err) {
      setError("Ошибка входа");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="card" onSubmit={handle}>
      <h2>Вход</h2>
      <label>
        Логин
        <input value={login} onChange={(e) => setLogin(e.target.value)} />
      </label>
      <label>
        Пароль
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? "Входим..." : "Войти"}
      </button>
    </form>
  );
}

function UsersTab({ data, refresh }) {
  return (
    <section>
      <div className="toolbar">
        <h3>Users</h3>
        <button onClick={refresh}>Обновить</button>
      </div>
      <div className="table">
        <div className="row head">
          <div>tg_user_id</div>
          <div>Имя</div>
          <div>username</div>
          <div>first_seen_at</div>
          <div>last_seen_at</div>
          <div>greetings</div>
        </div>
        {data.items?.map((u) => (
          <div className="row" key={u.tg_user_id}>
            <div>{u.tg_user_id}</div>
            <div>
              {[u.first_name, u.last_name].filter(Boolean).join(" ") || "—"}
            </div>
            <div>{u.username || "—"}</div>
            <div>{u.first_seen_at}</div>
            <div>{u.last_seen_at}</div>
            <div>{u.greetings_count}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function GreetingsTab({ data, refresh, filterUser, setFilterUser }) {
  return (
    <section>
      <div className="toolbar">
        <h3>Greetings</h3>
        <div className="filters">
          <input
            placeholder="tg_user_id"
            value={filterUser}
            onChange={(e) => setFilterUser(e.target.value)}
          />
        </div>
        <button onClick={refresh}>Обновить</button>
      </div>
      <div className="table">
        <div className="row head">
          <div>sent_at</div>
          <div>tg_user_id</div>
          <div>text</div>
        </div>
        {data.items?.map((g, idx) => (
          <div className="row" key={idx}>
            <div>{g.sent_at}</div>
            <div>{g.tg_user_id}</div>
            <div className="text">{g.greeting_text}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function MessagesTab({
  data,
  refresh,
  filterUser,
  setFilterUser,
  filterType,
  setFilterType,
}) {
  return (
    <section>
      <div className="toolbar">
        <h3>Messages</h3>
        <div className="filters">
          <input
            placeholder="tg_user_id"
            value={filterUser}
            onChange={(e) => setFilterUser(e.target.value)}
          />
          <input
            placeholder="type (text/sticker/...)"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          />
        </div>
        <button onClick={refresh}>Обновить</button>
      </div>
      <div className="table">
        <div className="row head">
          <div>received_at</div>
          <div>tg_user_id</div>
          <div>type</div>
          <div>text</div>
        </div>
        {data.items?.map((m, idx) => (
          <div className="row" key={idx}>
            <div>{m.received_at}</div>
            <div>{m.tg_user_id}</div>
            <div>{m.message_type}</div>
            <div className="text">{m.message_text || "—"}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState("users");
  const [users, setUsers] = useState({ items: [] });
  const [greetings, setGreetings] = useState({ items: [] });
  const [messages, setMessages] = useState({ items: [] });
  const [filterGreetingUser, setFilterGreetingUser] = useState("");
  const [filterMessageUser, setFilterMessageUser] = useState("");
  const [filterMessageType, setFilterMessageType] = useState("");
  const [wsStatus, setWsStatus] = useState("disconnected");

  const loadUsers = async () => {
    const data = await api("/api/users");
    setUsers(data);
  };
  const loadGreetings = async () => {
    const params = new URLSearchParams();
    if (filterGreetingUser) params.set("tg_user_id", filterGreetingUser);
    const data = await api(`/api/greetings?${params.toString()}`);
    setGreetings(data);
  };
  const loadMessages = async () => {
    const params = new URLSearchParams();
    if (filterMessageUser) params.set("tg_user_id", filterMessageUser);
    if (filterMessageType) params.set("message_type", filterMessageType);
    const data = await api(`/api/messages?${params.toString()}`);
    setMessages(data);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    if (activeTab === "greetings") loadGreetings();
  }, [activeTab, filterGreetingUser]);

  useEffect(() => {
    if (activeTab === "messages") loadMessages();
  }, [activeTab, filterMessageUser, filterMessageType]);

  useEffect(() => {
    let ws;
    let retry = 0;
    const connect = () => {
      setWsStatus("connecting");
      ws = new WebSocket(WS_BASE);
      ws.onopen = () => {
        setWsStatus("connected");
        retry = 0;
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "user_upserted") {
            loadUsers();
          }
          if (data.type === "greeting_sent") {
            loadGreetings();
          }
          if (data.type === "message_received") {
            loadMessages();
          }
        } catch (e) {
          console.error("ws parse", e);
        }
      };
      ws.onclose = () => {
        setWsStatus("disconnected");
        retry += 1;
        const delay = Math.min(5000, 500 * retry);
        setTimeout(connect, delay);
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => ws && ws.close();
  }, []);

  const tabContent = useMemo(() => {
    if (activeTab === "users")
      return <UsersTab data={users} refresh={loadUsers} />;
    if (activeTab === "greetings")
      return (
        <GreetingsTab
          data={greetings}
          refresh={loadGreetings}
          filterUser={filterGreetingUser}
          setFilterUser={setFilterGreetingUser}
        />
      );
    return (
      <MessagesTab
        data={messages}
        refresh={loadMessages}
        filterUser={filterMessageUser}
        setFilterUser={setFilterMessageUser}
        filterType={filterMessageType}
        setFilterType={setFilterMessageType}
      />
    );
  }, [
    activeTab,
    users,
    greetings,
    messages,
    filterGreetingUser,
    filterMessageUser,
    filterMessageType,
  ]);

  return (
    <div className="card">
      <header className="tabs">
        <div className="left">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={activeTab === t.id ? "active" : ""}
              onClick={() => setActiveTab(t.id)}
            >
              {t.title}
            </button>
          ))}
        </div>
        <button className="secondary" onClick={onLogout}>
          Выйти
        </button>
        <span className={`ws ws-${wsStatus}`}>WS: {wsStatus}</span>
      </header>
      {tabContent}
    </div>
  );
}

function App() {
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [error, setError] = useState("");

  const checkAuth = async () => {
    setError("");
    try {
      await api("/api/auth/me");
      setAuthed(true);
    } catch (e) {
      setAuthed(false);
    } finally {
      setReady(true);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const logout = async () => {
    await api("/api/auth/logout", { method: "POST" });
    setAuthed(false);
  };

  if (!ready) {
    return (
      <main className="page">
        <h1>NY Bot Admin</h1>
        <p>Загрузка...</p>
      </main>
    );
  }

  return (
    <main className="page">
      <h1>NY Bot Admin</h1>
      {!authed ? (
        <LoginForm onLogin={checkAuth} />
      ) : (
        <Dashboard onLogout={logout} />
      )}
      {error && <p className="error">{error}</p>}
    </main>
  );
}

export default App;

