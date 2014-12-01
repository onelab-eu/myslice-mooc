CREATE TABLE resources (
	hostname text UNIQUE,
	site text,
	ipv4 inet,
	ipv6 inet,
	mac macaddr,
	distro text,
	kernel text,
	cores integer,
	cpu text,
	ram text,
	disk text,
	PRIMARY KEY (hostname)
);

CREATE TABLE monitor (
		id serial,
		hostname text,
		status text, -- up, down, no access, disabled, maintenance
		timestamp timestamp,
	PRIMARY KEY (id),
	FOREIGN KEY (hostname)
		REFERENCES resources (hostname)
		ON UPDATE NO ACTION ON DELETE NO ACTION
);