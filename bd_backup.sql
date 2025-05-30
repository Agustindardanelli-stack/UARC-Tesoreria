PGDMP  5        
            }            tesoreria_bd    16.8 (Debian 16.8-1.pgdg120+1)    17.2 �    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            �           1262    16389    tesoreria_bd    DATABASE     w   CREATE DATABASE tesoreria_bd WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.UTF8';
    DROP DATABASE tesoreria_bd;
                     postgre    false            �           0    0    tesoreria_bd    DATABASE PROPERTIES     5   ALTER DATABASE tesoreria_bd SET "TimeZone" TO 'utc';
                          postgre    false                        2615    2200    public    SCHEMA        CREATE SCHEMA public;
    DROP SCHEMA public;
                     postgre    false            �           0    0    SCHEMA public    COMMENT     6   COMMENT ON SCHEMA public IS 'standard public schema';
                        postgre    false    6            �            1259    16435 	   auditoria    TABLE     I  CREATE TABLE public.auditoria (
    id integer NOT NULL,
    usuario_id integer,
    accion text NOT NULL,
    tabla_afectada text NOT NULL,
    registro_id integer NOT NULL,
    fecha timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    pago_id integer,
    cobranza_id integer,
    cuota_id integer,
    detalles text
);
    DROP TABLE public.auditoria;
       public         heap r       postgre    false    6            �            1259    16441    auditoria_id_seq    SEQUENCE     �   CREATE SEQUENCE public.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.auditoria_id_seq;
       public               postgre    false    6    216            �           0    0    auditoria_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.auditoria_id_seq OWNED BY public.auditoria.id;
          public               postgre    false    217            �            1259    16442 
   categorias    TABLE     h   CREATE TABLE public.categorias (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL
);
    DROP TABLE public.categorias;
       public         heap r       postgre    false    6            �            1259    16445    categorias_id_seq    SEQUENCE     �   CREATE SEQUENCE public.categorias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 (   DROP SEQUENCE public.categorias_id_seq;
       public               postgre    false    6    218            �           0    0    categorias_id_seq    SEQUENCE OWNED BY     G   ALTER SEQUENCE public.categorias_id_seq OWNED BY public.categorias.id;
          public               postgre    false    219            �            1259    16446 	   cobranzas    TABLE     >  CREATE TABLE public.cobranzas (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    fecha date NOT NULL,
    monto numeric(10,2) NOT NULL,
    transaccion_id integer,
    email_enviado boolean DEFAULT false,
    fecha_envio_email timestamp without time zone,
    email_destinatario character varying(100)
);
    DROP TABLE public.cobranzas;
       public         heap r       postgre    false    6            �           0    0    COLUMN cobranzas.email_enviado    COMMENT     a   COMMENT ON COLUMN public.cobranzas.email_enviado IS 'Indica si el recibo fue enviado por email';
          public               postgre    false    220            �           0    0 "   COLUMN cobranzas.fecha_envio_email    COMMENT     m   COMMENT ON COLUMN public.cobranzas.fecha_envio_email IS 'Fecha y hora en que se envió el recibo por email';
          public               postgre    false    220            �           0    0 #   COLUMN cobranzas.email_destinatario    COMMENT     m   COMMENT ON COLUMN public.cobranzas.email_destinatario IS 'Dirección de email a la que se envió el recibo';
          public               postgre    false    220            �            1259    16450    cobranzas_id_seq    SEQUENCE     �   CREATE SEQUENCE public.cobranzas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 '   DROP SEQUENCE public.cobranzas_id_seq;
       public               postgre    false    220    6            �           0    0    cobranzas_id_seq    SEQUENCE OWNED BY     E   ALTER SEQUENCE public.cobranzas_id_seq OWNED BY public.cobranzas.id;
          public               postgre    false    221            �            1259    16451    cuota    TABLE     a  CREATE TABLE public.cuota (
    id integer NOT NULL,
    usuario_id integer,
    fecha date NOT NULL,
    monto numeric(10,2) NOT NULL,
    pagado boolean DEFAULT false,
    monto_pagado numeric(10,2) DEFAULT 0,
    email_enviado boolean DEFAULT false,
    fecha_envio_email timestamp without time zone,
    email_destinatario character varying(100)
);
    DROP TABLE public.cuota;
       public         heap r       postgre    false    6            �            1259    16456    cuota_societaria_id_seq    SEQUENCE     �   CREATE SEQUENCE public.cuota_societaria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.cuota_societaria_id_seq;
       public               postgre    false    6    222            �           0    0    cuota_societaria_id_seq    SEQUENCE OWNED BY     H   ALTER SEQUENCE public.cuota_societaria_id_seq OWNED BY public.cuota.id;
          public               postgre    false    223            �            1259    16457    email_config    TABLE     I  CREATE TABLE public.email_config (
    id integer NOT NULL,
    smtp_server character varying(100) NOT NULL,
    smtp_port integer NOT NULL,
    smtp_username character varying(100) NOT NULL,
    smtp_password character varying(100) NOT NULL,
    email_from character varying(100) NOT NULL,
    is_active boolean DEFAULT true
);
     DROP TABLE public.email_config;
       public         heap r       postgre    false    6            �           0    0    TABLE email_config    COMMENT     S   COMMENT ON TABLE public.email_config IS 'Configuración para el envío de emails';
          public               postgre    false    224            �           0    0    COLUMN email_config.smtp_server    COMMENT     ]   COMMENT ON COLUMN public.email_config.smtp_server IS 'Servidor SMTP para envío de correos';
          public               postgre    false    224            �           0    0    COLUMN email_config.smtp_port    COMMENT     O   COMMENT ON COLUMN public.email_config.smtp_port IS 'Puerto del servidor SMTP';
          public               postgre    false    224            �           0    0 !   COLUMN email_config.smtp_username    COMMENT     [   COMMENT ON COLUMN public.email_config.smtp_username IS 'Usuario para autenticación SMTP';
          public               postgre    false    224            �           0    0 !   COLUMN email_config.smtp_password    COMMENT     _   COMMENT ON COLUMN public.email_config.smtp_password IS 'Contraseña para autenticación SMTP';
          public               postgre    false    224            �           0    0    COLUMN email_config.email_from    COMMENT     V   COMMENT ON COLUMN public.email_config.email_from IS 'Dirección de correo remitente';
          public               postgre    false    224            �           0    0    COLUMN email_config.is_active    COMMENT     a   COMMENT ON COLUMN public.email_config.is_active IS 'Indica si esta configuración está activa';
          public               postgre    false    224            �            1259    16461    email_config_id_seq    SEQUENCE     �   CREATE SEQUENCE public.email_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.email_config_id_seq;
       public               postgre    false    224    6            �           0    0    email_config_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.email_config_id_seq OWNED BY public.email_config.id;
          public               postgre    false    225            �            1259    16462    pagos    TABLE     T  CREATE TABLE public.pagos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    fecha date NOT NULL,
    monto numeric(10,2) NOT NULL,
    retencion_id integer,
    transaccion_id integer,
    email_enviado boolean DEFAULT false,
    fecha_envio_email timestamp without time zone,
    email_destinatario character varying(100)
);
    DROP TABLE public.pagos;
       public         heap r       postgre    false    6            �            1259    16465    pagos_id_seq    SEQUENCE     �   CREATE SEQUENCE public.pagos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.pagos_id_seq;
       public               postgre    false    226    6            �           0    0    pagos_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.pagos_id_seq OWNED BY public.pagos.id;
          public               postgre    false    227            �            1259    16466    partidas    TABLE     w  CREATE TABLE public.partidas (
    id integer NOT NULL,
    fecha date NOT NULL,
    cuenta character varying(50) NOT NULL,
    detalle character varying(255),
    recibo_factura character varying(50),
    ingreso numeric(10,2) DEFAULT 0 NOT NULL,
    egreso numeric(10,2) DEFAULT 0 NOT NULL,
    saldo numeric(10,2) NOT NULL,
    usuario_id integer NOT NULL,
    cobranza_id integer,
    pago_id integer,
    monto numeric(10,2) NOT NULL,
    tipo character varying(10) NOT NULL,
    CONSTRAINT partidas_tipo_check CHECK (((tipo)::text = ANY (ARRAY[('ingreso'::character varying)::text, ('egreso'::character varying)::text])))
);
    DROP TABLE public.partidas;
       public         heap r       postgre    false    6            �            1259    16472    partidas_id_seq    SEQUENCE     �   CREATE SEQUENCE public.partidas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.partidas_id_seq;
       public               postgre    false    228    6            �           0    0    partidas_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.partidas_id_seq OWNED BY public.partidas.id;
          public               postgre    false    229            �            1259    16473    retenciones    TABLE     �   CREATE TABLE public.retenciones (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    monto numeric(10,2) NOT NULL
);
    DROP TABLE public.retenciones;
       public         heap r       postgre    false    6            �            1259    16476    retenciones_division    TABLE     �   CREATE TABLE public.retenciones_division (
    id integer NOT NULL,
    retencion_id integer NOT NULL,
    categoria_id integer
);
 (   DROP TABLE public.retenciones_division;
       public         heap r       postgre    false    6            �            1259    16479    retenciones_division_id_seq    SEQUENCE     �   CREATE SEQUENCE public.retenciones_division_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.retenciones_division_id_seq;
       public               postgre    false    6    231            �           0    0    retenciones_division_id_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.retenciones_division_id_seq OWNED BY public.retenciones_division.id;
          public               postgre    false    232            �            1259    16480    retenciones_id_seq    SEQUENCE     �   CREATE SEQUENCE public.retenciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.retenciones_id_seq;
       public               postgre    false    230    6            �           0    0    retenciones_id_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.retenciones_id_seq OWNED BY public.retenciones.id;
          public               postgre    false    233            �            1259    16481    roles    TABLE     b   CREATE TABLE public.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);
    DROP TABLE public.roles;
       public         heap r       postgre    false    6            �            1259    16484    roles_id_seq    SEQUENCE     �   CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.roles_id_seq;
       public               postgre    false    234    6            �           0    0    roles_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;
          public               postgre    false    235            �            1259    16485    transacciones    TABLE     �  CREATE TABLE public.transacciones (
    id integer NOT NULL,
    tipo character varying(10) NOT NULL,
    monto numeric(10,2) NOT NULL,
    fecha date DEFAULT CURRENT_DATE NOT NULL,
    usuario_id integer,
    referencia text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT transacciones_tipo_check CHECK (((tipo)::text = ANY (ARRAY[('ingreso'::character varying)::text, ('egreso'::character varying)::text])))
);
 !   DROP TABLE public.transacciones;
       public         heap r       postgre    false    6            �            1259    16493    transacciones_id_seq    SEQUENCE     �   CREATE SEQUENCE public.transacciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.transacciones_id_seq;
       public               postgre    false    6    236            �           0    0    transacciones_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.transacciones_id_seq OWNED BY public.transacciones.id;
          public               postgre    false    237            �            1259    16494    usuarios    TABLE     �   CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash text,
    rol_id integer NOT NULL
);
    DROP TABLE public.usuarios;
       public         heap r       postgre    false    6            �            1259    16499    usuarios_id_seq    SEQUENCE     �   CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.usuarios_id_seq;
       public               postgre    false    6    238            �           0    0    usuarios_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;
          public               postgre    false    239            �           2604    16500    auditoria id    DEFAULT     l   ALTER TABLE ONLY public.auditoria ALTER COLUMN id SET DEFAULT nextval('public.auditoria_id_seq'::regclass);
 ;   ALTER TABLE public.auditoria ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    217    216            �           2604    16501    categorias id    DEFAULT     n   ALTER TABLE ONLY public.categorias ALTER COLUMN id SET DEFAULT nextval('public.categorias_id_seq'::regclass);
 <   ALTER TABLE public.categorias ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    219    218            �           2604    16502    cobranzas id    DEFAULT     l   ALTER TABLE ONLY public.cobranzas ALTER COLUMN id SET DEFAULT nextval('public.cobranzas_id_seq'::regclass);
 ;   ALTER TABLE public.cobranzas ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    221    220            �           2604    16503    cuota id    DEFAULT     o   ALTER TABLE ONLY public.cuota ALTER COLUMN id SET DEFAULT nextval('public.cuota_societaria_id_seq'::regclass);
 7   ALTER TABLE public.cuota ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    223    222            �           2604    16504    email_config id    DEFAULT     r   ALTER TABLE ONLY public.email_config ALTER COLUMN id SET DEFAULT nextval('public.email_config_id_seq'::regclass);
 >   ALTER TABLE public.email_config ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    225    224            �           2604    16505    pagos id    DEFAULT     d   ALTER TABLE ONLY public.pagos ALTER COLUMN id SET DEFAULT nextval('public.pagos_id_seq'::regclass);
 7   ALTER TABLE public.pagos ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    227    226            �           2604    16506    partidas id    DEFAULT     j   ALTER TABLE ONLY public.partidas ALTER COLUMN id SET DEFAULT nextval('public.partidas_id_seq'::regclass);
 :   ALTER TABLE public.partidas ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    229    228            �           2604    16507    retenciones id    DEFAULT     p   ALTER TABLE ONLY public.retenciones ALTER COLUMN id SET DEFAULT nextval('public.retenciones_id_seq'::regclass);
 =   ALTER TABLE public.retenciones ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    233    230            �           2604    16508    retenciones_division id    DEFAULT     �   ALTER TABLE ONLY public.retenciones_division ALTER COLUMN id SET DEFAULT nextval('public.retenciones_division_id_seq'::regclass);
 F   ALTER TABLE public.retenciones_division ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    232    231            �           2604    16509    roles id    DEFAULT     d   ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);
 7   ALTER TABLE public.roles ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    235    234            �           2604    16510    transacciones id    DEFAULT     t   ALTER TABLE ONLY public.transacciones ALTER COLUMN id SET DEFAULT nextval('public.transacciones_id_seq'::regclass);
 ?   ALTER TABLE public.transacciones ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    237    236            �           2604    16511    usuarios id    DEFAULT     j   ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);
 :   ALTER TABLE public.usuarios ALTER COLUMN id DROP DEFAULT;
       public               postgre    false    239    238            �          0    16435 	   auditoria 
   TABLE DATA           �   COPY public.auditoria (id, usuario_id, accion, tabla_afectada, registro_id, fecha, pago_id, cobranza_id, cuota_id, detalles) FROM stdin;
    public               postgre    false    216   �       �          0    16442 
   categorias 
   TABLE DATA           0   COPY public.categorias (id, nombre) FROM stdin;
    public               postgre    false    218   ��       �          0    16446 	   cobranzas 
   TABLE DATA           �   COPY public.cobranzas (id, usuario_id, fecha, monto, transaccion_id, email_enviado, fecha_envio_email, email_destinatario) FROM stdin;
    public               postgre    false    220   �       �          0    16451    cuota 
   TABLE DATA           �   COPY public.cuota (id, usuario_id, fecha, monto, pagado, monto_pagado, email_enviado, fecha_envio_email, email_destinatario) FROM stdin;
    public               postgre    false    222   
�       �          0    16457    email_config 
   TABLE DATA           w   COPY public.email_config (id, smtp_server, smtp_port, smtp_username, smtp_password, email_from, is_active) FROM stdin;
    public               postgre    false    224   A�       �          0    16462    pagos 
   TABLE DATA           �   COPY public.pagos (id, usuario_id, fecha, monto, retencion_id, transaccion_id, email_enviado, fecha_envio_email, email_destinatario) FROM stdin;
    public               postgre    false    226   ��       �          0    16466    partidas 
   TABLE DATA           �   COPY public.partidas (id, fecha, cuenta, detalle, recibo_factura, ingreso, egreso, saldo, usuario_id, cobranza_id, pago_id, monto, tipo) FROM stdin;
    public               postgre    false    228   j�       �          0    16473    retenciones 
   TABLE DATA           8   COPY public.retenciones (id, nombre, monto) FROM stdin;
    public               postgre    false    230   b�       �          0    16476    retenciones_division 
   TABLE DATA           N   COPY public.retenciones_division (id, retencion_id, categoria_id) FROM stdin;
    public               postgre    false    231   ̪       �          0    16481    roles 
   TABLE DATA           +   COPY public.roles (id, nombre) FROM stdin;
    public               postgre    false    234   ��       �          0    16485    transacciones 
   TABLE DATA           c   COPY public.transacciones (id, tipo, monto, fecha, usuario_id, referencia, created_at) FROM stdin;
    public               postgre    false    236   1�       �          0    16494    usuarios 
   TABLE DATA           L   COPY public.usuarios (id, nombre, email, password_hash, rol_id) FROM stdin;
    public               postgre    false    238   N�       �           0    0    auditoria_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.auditoria_id_seq', 3, true);
          public               postgre    false    217            �           0    0    categorias_id_seq    SEQUENCE SET     @   SELECT pg_catalog.setval('public.categorias_id_seq', 1, false);
          public               postgre    false    219            �           0    0    cobranzas_id_seq    SEQUENCE SET     ?   SELECT pg_catalog.setval('public.cobranzas_id_seq', 53, true);
          public               postgre    false    221            �           0    0    cuota_societaria_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.cuota_societaria_id_seq', 19, true);
          public               postgre    false    223            �           0    0    email_config_id_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.email_config_id_seq', 1, true);
          public               postgre    false    225            �           0    0    pagos_id_seq    SEQUENCE SET     ;   SELECT pg_catalog.setval('public.pagos_id_seq', 29, true);
          public               postgre    false    227            �           0    0    partidas_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.partidas_id_seq', 83, true);
          public               postgre    false    229                        0    0    retenciones_division_id_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.retenciones_division_id_seq', 1, false);
          public               postgre    false    232                       0    0    retenciones_id_seq    SEQUENCE SET     @   SELECT pg_catalog.setval('public.retenciones_id_seq', 3, true);
          public               postgre    false    233                       0    0    roles_id_seq    SEQUENCE SET     :   SELECT pg_catalog.setval('public.roles_id_seq', 3, true);
          public               postgre    false    235                       0    0    transacciones_id_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.transacciones_id_seq', 1, false);
          public               postgre    false    237                       0    0    usuarios_id_seq    SEQUENCE SET     >   SELECT pg_catalog.setval('public.usuarios_id_seq', 26, true);
          public               postgre    false    239            �           2606    16513    auditoria auditoria_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT auditoria_pkey;
       public                 postgre    false    216                       2606    16515    categorias categorias_pkey 
   CONSTRAINT     X   ALTER TABLE ONLY public.categorias
    ADD CONSTRAINT categorias_pkey PRIMARY KEY (id);
 D   ALTER TABLE ONLY public.categorias DROP CONSTRAINT categorias_pkey;
       public                 postgre    false    218                       2606    16517    cobranzas cobranzas_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.cobranzas
    ADD CONSTRAINT cobranzas_pkey PRIMARY KEY (id);
 B   ALTER TABLE ONLY public.cobranzas DROP CONSTRAINT cobranzas_pkey;
       public                 postgre    false    220                       2606    16519    cuota cuota_societaria_pkey 
   CONSTRAINT     Y   ALTER TABLE ONLY public.cuota
    ADD CONSTRAINT cuota_societaria_pkey PRIMARY KEY (id);
 E   ALTER TABLE ONLY public.cuota DROP CONSTRAINT cuota_societaria_pkey;
       public                 postgre    false    222            	           2606    16521    email_config email_config_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.email_config
    ADD CONSTRAINT email_config_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.email_config DROP CONSTRAINT email_config_pkey;
       public                 postgre    false    224                       2606    16523    pagos pagos_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.pagos DROP CONSTRAINT pagos_pkey;
       public                 postgre    false    226                       2606    16525    partidas partidas_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.partidas
    ADD CONSTRAINT partidas_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.partidas DROP CONSTRAINT partidas_pkey;
       public                 postgre    false    228                       2606    16527 .   retenciones_division retenciones_division_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.retenciones_division
    ADD CONSTRAINT retenciones_division_pkey PRIMARY KEY (id);
 X   ALTER TABLE ONLY public.retenciones_division DROP CONSTRAINT retenciones_division_pkey;
       public                 postgre    false    231                       2606    16529    retenciones retenciones_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.retenciones
    ADD CONSTRAINT retenciones_pkey PRIMARY KEY (id);
 F   ALTER TABLE ONLY public.retenciones DROP CONSTRAINT retenciones_pkey;
       public                 postgre    false    230                       2606    16531    roles roles_nombre_key 
   CONSTRAINT     S   ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);
 @   ALTER TABLE ONLY public.roles DROP CONSTRAINT roles_nombre_key;
       public                 postgre    false    234                       2606    16533    roles roles_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.roles DROP CONSTRAINT roles_pkey;
       public                 postgre    false    234                       2606    16535     transacciones transacciones_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.transacciones
    ADD CONSTRAINT transacciones_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.transacciones DROP CONSTRAINT transacciones_pkey;
       public                 postgre    false    236                       2606    16537    usuarios unique_nombre 
   CONSTRAINT     S   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT unique_nombre UNIQUE (nombre);
 @   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT unique_nombre;
       public                 postgre    false    238                       2606    16539    usuarios usuarios_email_key 
   CONSTRAINT     W   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);
 E   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_email_key;
       public                 postgre    false    238                       2606    16541    usuarios usuarios_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_pkey;
       public                 postgre    false    238            �           1259    16656    idx_auditoria_cobranza    INDEX     S   CREATE INDEX idx_auditoria_cobranza ON public.auditoria USING btree (cobranza_id);
 *   DROP INDEX public.idx_auditoria_cobranza;
       public                 postgre    false    216            �           1259    16657    idx_auditoria_cuota    INDEX     M   CREATE INDEX idx_auditoria_cuota ON public.auditoria USING btree (cuota_id);
 '   DROP INDEX public.idx_auditoria_cuota;
       public                 postgre    false    216                        1259    16655    idx_auditoria_pago    INDEX     K   CREATE INDEX idx_auditoria_pago ON public.auditoria USING btree (pago_id);
 &   DROP INDEX public.idx_auditoria_pago;
       public                 postgre    false    216                       1259    16542    idx_cobranzas_email_enviado    INDEX     Z   CREATE INDEX idx_cobranzas_email_enviado ON public.cobranzas USING btree (email_enviado);
 /   DROP INDEX public.idx_cobranzas_email_enviado;
       public                 postgre    false    220                       2606    16543 #   auditoria auditoria_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;
 M   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT auditoria_usuario_id_fkey;
       public               postgre    false    238    216    3357            "           2606    16548 '   cobranzas cobranzas_transaccion_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.cobranzas
    ADD CONSTRAINT cobranzas_transaccion_id_fkey FOREIGN KEY (transaccion_id) REFERENCES public.transacciones(id);
 Q   ALTER TABLE ONLY public.cobranzas DROP CONSTRAINT cobranzas_transaccion_id_fkey;
       public               postgre    false    3351    220    236            #           2606    16553 #   cobranzas cobranzas_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.cobranzas
    ADD CONSTRAINT cobranzas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;
 M   ALTER TABLE ONLY public.cobranzas DROP CONSTRAINT cobranzas_usuario_id_fkey;
       public               postgre    false    3357    220    238            %           2606    16558 &   cuota cuota_societaria_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.cuota
    ADD CONSTRAINT cuota_societaria_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 P   ALTER TABLE ONLY public.cuota DROP CONSTRAINT cuota_societaria_usuario_id_fkey;
       public               postgre    false    238    3357    222                       2606    16645    auditoria fk_auditoria_cobranza    FK CONSTRAINT     �   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT fk_auditoria_cobranza FOREIGN KEY (cobranza_id) REFERENCES public.cobranzas(id) ON DELETE SET NULL;
 I   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT fk_auditoria_cobranza;
       public               postgre    false    3332    220    216                        2606    16650    auditoria fk_auditoria_cuota    FK CONSTRAINT     �   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT fk_auditoria_cuota FOREIGN KEY (cuota_id) REFERENCES public.cuota(id) ON DELETE SET NULL;
 F   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT fk_auditoria_cuota;
       public               postgre    false    3335    216    222            !           2606    16640    auditoria fk_auditoria_pago    FK CONSTRAINT     �   ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT fk_auditoria_pago FOREIGN KEY (pago_id) REFERENCES public.pagos(id) ON DELETE SET NULL;
 E   ALTER TABLE ONLY public.auditoria DROP CONSTRAINT fk_auditoria_pago;
       public               postgre    false    3339    226    216            $           2606    16563    cobranzas fk_cobranzas_usuario    FK CONSTRAINT     �   ALTER TABLE ONLY public.cobranzas
    ADD CONSTRAINT fk_cobranzas_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 H   ALTER TABLE ONLY public.cobranzas DROP CONSTRAINT fk_cobranzas_usuario;
       public               postgre    false    220    238    3357            &           2606    16568    cuota fk_cuota_usuario    FK CONSTRAINT     {   ALTER TABLE ONLY public.cuota
    ADD CONSTRAINT fk_cuota_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 @   ALTER TABLE ONLY public.cuota DROP CONSTRAINT fk_cuota_usuario;
       public               postgre    false    3357    222    238            (           2606    16573    pagos fk_pagos_usuario    FK CONSTRAINT     {   ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT fk_pagos_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 @   ALTER TABLE ONLY public.pagos DROP CONSTRAINT fk_pagos_usuario;
       public               postgre    false    3357    238    226            ,           2606    16578    partidas fk_partidas_cobranza    FK CONSTRAINT     �   ALTER TABLE ONLY public.partidas
    ADD CONSTRAINT fk_partidas_cobranza FOREIGN KEY (cobranza_id) REFERENCES public.cobranzas(id) ON DELETE SET NULL;
 G   ALTER TABLE ONLY public.partidas DROP CONSTRAINT fk_partidas_cobranza;
       public               postgre    false    220    228    3332            -           2606    16583    partidas fk_partidas_pago    FK CONSTRAINT     �   ALTER TABLE ONLY public.partidas
    ADD CONSTRAINT fk_partidas_pago FOREIGN KEY (pago_id) REFERENCES public.pagos(id) ON DELETE SET NULL;
 C   ALTER TABLE ONLY public.partidas DROP CONSTRAINT fk_partidas_pago;
       public               postgre    false    226    3339    228            .           2606    16588    partidas fk_partidas_usuario    FK CONSTRAINT     �   ALTER TABLE ONLY public.partidas
    ADD CONSTRAINT fk_partidas_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);
 F   ALTER TABLE ONLY public.partidas DROP CONSTRAINT fk_partidas_usuario;
       public               postgre    false    238    3357    228            '           2606    16593    cuota fk_usuario    FK CONSTRAINT     �   ALTER TABLE ONLY public.cuota
    ADD CONSTRAINT fk_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;
 :   ALTER TABLE ONLY public.cuota DROP CONSTRAINT fk_usuario;
       public               postgre    false    3357    238    222            3           2606    16598    usuarios fk_usuarios_roles    FK CONSTRAINT     x   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_usuarios_roles FOREIGN KEY (rol_id) REFERENCES public.roles(id);
 D   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT fk_usuarios_roles;
       public               postgre    false    3349    234    238            )           2606    16603    pagos pagos_retencion_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_retencion_id_fkey FOREIGN KEY (retencion_id) REFERENCES public.retenciones(id) ON DELETE CASCADE;
 G   ALTER TABLE ONLY public.pagos DROP CONSTRAINT pagos_retencion_id_fkey;
       public               postgre    false    230    226    3343            *           2606    16608    pagos pagos_transaccion_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_transaccion_id_fkey FOREIGN KEY (transaccion_id) REFERENCES public.transacciones(id);
 I   ALTER TABLE ONLY public.pagos DROP CONSTRAINT pagos_transaccion_id_fkey;
       public               postgre    false    226    3351    236            +           2606    16613    pagos pagos_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.pagos
    ADD CONSTRAINT pagos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;
 E   ALTER TABLE ONLY public.pagos DROP CONSTRAINT pagos_usuario_id_fkey;
       public               postgre    false    238    3357    226            /           2606    16618 !   partidas partidas_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.partidas
    ADD CONSTRAINT partidas_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;
 K   ALTER TABLE ONLY public.partidas DROP CONSTRAINT partidas_usuario_id_fkey;
       public               postgre    false    228    3357    238            0           2606    16623 ;   retenciones_division retenciones_division_categoria_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.retenciones_division
    ADD CONSTRAINT retenciones_division_categoria_id_fkey FOREIGN KEY (categoria_id) REFERENCES public.categorias(id) ON DELETE CASCADE;
 e   ALTER TABLE ONLY public.retenciones_division DROP CONSTRAINT retenciones_division_categoria_id_fkey;
       public               postgre    false    3330    231    218            1           2606    16628 ;   retenciones_division retenciones_division_retencion_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.retenciones_division
    ADD CONSTRAINT retenciones_division_retencion_id_fkey FOREIGN KEY (retencion_id) REFERENCES public.retenciones(id) ON DELETE CASCADE;
 e   ALTER TABLE ONLY public.retenciones_division DROP CONSTRAINT retenciones_division_retencion_id_fkey;
       public               postgre    false    231    3343    230            2           2606    16633 +   transacciones transacciones_usuario_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.transacciones
    ADD CONSTRAINT transacciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE SET NULL;
 U   ALTER TABLE ONLY public.transacciones DROP CONSTRAINT transacciones_usuario_id_fkey;
       public               postgre    false    238    3357    236            �   �   x���A�0�u9E/@3�vdJ����)����ky/f��@��������,�����z�"����dR6�(K�%ie�4���is{��2���Cs��,�,�^{d
&�e�-��q��ёq%U���S�s��5�rp�.�'�V���@$ 6&�m�(�ʲ���S.      �   A   x�3���KK�+���*-K���I-�2�(��M-JTp�,�,�<�9�˘�17��$�8��+F��� >K'      �   �  x���]n"1���)� �'O=AO�jw+$ڕ���o 	�d��H3���8$���  ��k�}|l_W�B 	|%0�HH�#����#��<���sD:�q�Ȯ�Br�Ю���iE�Q��pͅ,00� ��8��U/ �[�R�E$���y��!�[����}��zf��ͱ�g=�����!4�#f☏�K�/!�d�����&� ��SJv���_﻿ﻯ_�þ�||������sժ7��+VNQR6@�JO�+C�vВ:V��H� f��ő��"W�����c�'�R)G0&ˎ5=a�U-��0{�<��F���1���T--�$����X���4����]R�1m`㔠� �!}�5a�S��K����h�S�E��+�r��9W��Z�z����UM1Y����Kg�����_P̜�{`-�c	;F�!6B�,3=��Fn�Ţ��9K�=�'�xr��p�*F�E��n�j��4�)�      �   '  x���[N�0E�'�`����+`��(T�Z���CBҚRɒG�љ;�0��H=3":Dx���<��)�
* �ӿ�V`�@_���=���
fD��Q������ �=���o�EgR�i`�T2�4��eG6�K�|�c�$ْC�����i��޶����O���?���cGV�	�)��R�>�:���%�Z�2��S\�s�c����\ﮖfNN8x/����3R9.ySj%���iR.Յ�,�wQCj�c-�y�rm�\�2Sr1�i�9S��)-]M-�WA'�+ٸ��>���      �   d   x�3�,�-)�K�M���K���4�0�,��LILI,J�,)�/.��O.M,*�w@��L�,RHL�,T(L��S�,�.��RHIUp��T��g� ;��=... .�0�      �   �  x���Yj�@D�G��4�>�WN���d��$���i�N")��!�T�)JՍ-��@=Y@� ���.<��]��(�D8�?5�c
��Q�4?��al����ǚ�{�(�g�c9����|X��I�~���>G_nP*�Is���_��ׇ�����q�ߕ���n��^:ċ���
Ĕdjp��Pv.mq�\ZS.VJ�S�bb����~�2V��h+_=����v�*�TvΣx(*H��g�I��q�F@Qi`����H���vs�Ff\8�9��\�T战R��W����1�5�4#������1x`�\�;&�k�1s��c-Ka��Ň���CA:'�S5~EL[��욈�5f!i�2J�sX�+|E�h(C�;;:�/�eX��ؘ<*�u��b��DjX�Į��
�      �   �  x����n�6���Sp��B^�j�f2h��$H��f��j���=�y����b��b�+���A��Ǔ�{��M䌊����v�\��:���dQ���v�)+�!�yU,�e��s�(�)�I�D�i�UV�u��<��(��]-_г�L�`S��c<z<Φ^�����勳�Z=;�c���u�F�UY��M�o�o6�-%�k��������*��6_��|LɺX�fB�_��~D&�F��T)��)/��N���_������x��6�����hg��@e��y\0NS��L�LA��n<50�}�j��e^��Ǜ��*%O��1�P�d6@�@g)��!�P)Pw���&%�ui�dY>�E��|���3��7���TR��cÉnBMrS����vm�	c�uP.�J��.����]I��MQ��?��ȕ]}]�]���媨�ݘ,a������-d��w6!h��A_�v�K�쒲˝��$h ��y�)�X����C�~��m�����ʙ@��*_{����ҷ�DÅ {��z ���_�����ȫE�9 !��U��V�<`�@�ϙJ�W��]>��9�ќ�N��~�~�{�~�k��Y�da��j"hlg�6�O2t�g��"s���Ee����v ��N����;?�Qx?)X�G�p��|\���W���*���W8ۭs�n�tG�U�(��>/��%���̫���Wx��%���Ѭ�>��`s6K 'd'+����C���_�eW�ĝ�6�[t�Q\ɡ������������#䊂�����c�Q�)���r,����.32����39��_WZ!�.�&#k�	��,l4�\���S��SX�lq�\�P[�����E#給 M��&���6]�ݽ)�����y,:럁D6���h�Iq�Q�Aw�A�D�3�f�l8"2?�F/���,D+kA�.�8��N~��f]�'��Ԟ;���O��|�K��=���+��{��3	�IƉ���%F���lb���:U͉ڱ=M��<���o��l�
�����	�Y�����8b��a��dt̙X�d]�'�����z��tT��n���){&�<z�Q��4U��6�Q�B�ڷ��);& d���A*�)nd�|��z����tq6:C��p:���	��������v����eѽ"�����6U���[.;�b���A{K�SM��E�ܲ�v�+�M-3��A����iF���ml�,��j������ �p��h����3��F��^\\�8�;W      �   Z   x�3�J-I�K�<�9O�3/-1�$_׫�,5/3'������@����YY@QfnjQ��KfYf1H����Y�cnfqI~q~1�T:F��� ��%�      �      x�3�4���2�4QƜ� *F��� 9�'      �   (   x�3�LL����2�,I-�/J-��2�L,J�,�b���� ��	�      �      x������ � �      �     x�m�K��:���W��5r�]+��"�xf%J0$6W�����s����*_�&Ua`��1?���R�&��191�|�:<�9_�Z�����~�DOo��udo�L����D� �DX����2�:C�+�Q�z���K��jy1�v���-,��g�-Mx�CԬ��mO��Eb��#�Ar�������#"��+��l���`N,V#�x�]4����x���S��9+�6<
aup���	�0� E�ྎH��K�,�݉�-�F��6�f�����/�� ����FJW5N:U�{�\m����Kyw���\���o:���7r�JO�-�̱Gڔ��M���)՝3�񸰘��5�"A��݉2(P�2����?��ʘ)�� �B�*M��Ki����M=U��G�,Sco8���0N@�
�Q���
?n��[�N�S��$8�h�yy;��Dj�Uъ%�����i=�r��/Uz���`z%�����_�ok�,�:���������@P��V�����bH缊�`ʲ3��o2
��kJ��3ɟ��.X���{ �U��ɑ��[Ҩ+y��J��޳��"�Qף�\��ja�]&�w��=���8x�;��U	.s'�;�+�puiߚ�i�%PP�&/a�ٲD���2���f�	�m�g~Y�5z\]ȡ��^'+]�ߖm�es� ���笍���'���}�b�X����\��a���N���+�DJ�4qrj�Z��_\���l�     