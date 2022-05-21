--
-- PostgreSQL database dump
--

-- Dumped from database version 14.3 (Debian 14.3-1.pgdg110+1)
-- Dumped by pg_dump version 14.3 (Debian 14.3-1.pgdg110+1)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now(),
    instashid text,
    itemid text,
    itemclass text,
    basetype text,
    rarity smallint,
    ilvl smallint,
    implicitmods text[],
    explicitmods text[],
    fracturedmods text[],
    corrupted boolean,
    price text,
    stash_id integer REFERENCES stash(id);
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.items_id_seq OWNER TO postgres;

--
-- Name: items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.items_id_seq OWNED BY public.items.id;


--
-- Name: stash; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stash (
    id integer NOT NULL,
    ts timestamp without time zone DEFAULT now(),
    stashid text,
    accountname text,
    stash text,
    league text
);


ALTER TABLE public.stash OWNER TO postgres;

--
-- Name: stash_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.stash_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stash_id_seq OWNER TO postgres;

--
-- Name: stash_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.stash_id_seq OWNED BY public.stash.id;


--
-- Name: items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN id SET DEFAULT nextval('public.items_id_seq'::regclass);


--
-- Name: stash id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stash ALTER COLUMN id SET DEFAULT nextval('public.stash_id_seq'::regclass);


--
-- PostgreSQL database dump complete
--

