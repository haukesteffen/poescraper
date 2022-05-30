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
-- Name: item_deltas; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.item_deltas AS
 SELECT s1.id AS s1_id,
    s1.ts AS s1_ts,
    ( SELECT s2.ts
           FROM public.stash s2
          WHERE ((s2.id > s1.id) AND (s2.stashid = s1.stashid))
          ORDER BY s2.id
         LIMIT 1) AS next_ts,
    s1.stashid AS s1_stashid
   FROM public.stash s1;


ALTER TABLE public.item_deltas OWNER TO postgres;

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
    stash_id integer
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
-- Name: pending_items; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.pending_items AS
 SELECT d.s1_id,
    d.s1_ts,
    d.next_ts,
    d.s1_stashid,
    i.ts AS item_ts,
    i.id AS item_id,
    i.stash_id AS item_stash_id
   FROM (public.item_deltas d
     JOIN public.items i ON (((d.s1_stashid = i.instashid) AND (i.ts > d.s1_ts) AND (i.ts < d.next_ts))));


ALTER TABLE public.pending_items OWNER TO postgres;

--
-- Name: pending_items_no_end; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.pending_items_no_end AS
 SELECT d.s1_id,
    d.s1_ts,
    d.next_ts,
    d.s1_stashid,
    i.ts AS item_ts,
    i.id AS item_id,
    i.stash_id AS item_stash_id
   FROM (public.item_deltas d
     JOIN public.items i ON (((d.s1_stashid = i.instashid) AND (i.ts > d.s1_ts))));


ALTER TABLE public.pending_items_no_end OWNER TO postgres;

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
-- Name: stash stash_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stash
    ADD CONSTRAINT stash_id_key UNIQUE (id);


--
-- Name: items items_stash_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT items_stash_id_fkey FOREIGN KEY (stash_id) REFERENCES public.stash(id);


--
-- Name: TABLE stash; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.stash TO poeuser;


--
-- Name: TABLE items; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.items TO poeuser;


--
-- Name: SEQUENCE items_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.items_id_seq TO poeuser;


--
-- Name: SEQUENCE stash_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.stash_id_seq TO poeuser;


--
-- PostgreSQL database dump complete
--

