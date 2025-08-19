--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13
-- Dumped by pg_dump version 15.13

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, email, password_hash, full_name, role, is_active, is_verified, created_at, updated_at, last_login, failed_login_attempts, locked_until, permissions) FROM stdin;
1	admin	admin@openpolicy.com	$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/vHhHhHh	System Administrator	admin	t	t	2025-08-18 01:48:53.752684	2025-08-18 01:50:13.54016	\N	0	\N	{read,write,admin,delete,manage_users,manage_roles,view_audit_logs}
2	testadmin	testadmin@openpolicy.com	$2b$12$7KYis4sKLGoGDkd2Jf6xJe99FT9EwJSLRnlmnrIx4nT7jDNITF5By	Test Administrator	user	t	f	2025-08-18 15:55:59.30266	2025-08-18 15:56:05.50587	2025-08-18 15:56:05.50587	0	\N	{read}
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, user_id, action, resource, resource_id, ip_address, user_agent, request_data, response_status, "timestamp", session_id) FROM stdin;
2	2	user_registered	auth	\N	192.168.65.1	curl/8.7.1	\N	\N	2025-08-18 15:55:59.707716	\N
3	2	login_success	auth	\N	192.168.65.1	curl/8.7.1	\N	\N	2025-08-18 15:56:05.846328	\N
4	2	logout	auth	\N	192.168.65.1	curl/8.7.1	\N	\N	2025-08-18 15:56:36.337234	\N
\.


--
-- Data for Name: email_verification_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.email_verification_tokens (id, user_id, token_hash, expires_at, created_at, verified_at, is_verified) FROM stdin;
\.


--
-- Data for Name: password_reset_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.password_reset_tokens (id, user_id, token_hash, expires_at, created_at, used_at, is_used) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (id, role_name, description, permissions, created_at) FROM stdin;
1	admin	System Administrator	{read,write,admin,delete,manage_users,manage_roles,view_audit_logs}	2025-08-18 01:48:53.75178
2	user	Standard User	{read,write,edit_profile,change_password}	2025-08-18 01:48:53.75178
3	guest	Guest User	{read}	2025-08-18 01:48:53.75178
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_sessions (id, user_id, token_hash, refresh_token_hash, ip_address, user_agent, expires_at, created_at, last_used, is_revoked) FROM stdin;
\.


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 4, true);


--
-- Name: email_verification_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.email_verification_tokens_id_seq', 1, false);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.password_reset_tokens_id_seq', 1, false);


--
-- Name: user_roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_roles_id_seq', 3, true);


--
-- Name: user_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_sessions_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- PostgreSQL database dump complete
--

