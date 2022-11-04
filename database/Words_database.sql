drop table if exists word_learning;
drop table if exists word_usage;
drop table if exists word ;
drop table if exists users_list ;
drop table if exists list_rating;
drop table if exists user_added_list;
drop table if exists word_list cascade ;
drop table if exists user_db cascade;


create table user_db(
    user_login varchar(30) PRIMARY KEY,
    user_password varchar(255) NOT NULL,
    user_name varchar(50) DEFAULT 'NoName'
                );

create table word_list(
    id_list INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    name_list varchar(30) NOT NULL,
    user_login varchar(30) NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(user_login) REFERENCES user_db(user_login)
);

create table user_added_list(
    id_list int NOT NULL,
    user_login varchar(30) NOT NULL,
    FOREIGN KEY(id_list) REFERENCES word_list(id_list),
    FOREIGN KEY(user_login) REFERENCES user_db(user_login),
    PRIMARY KEY(id_list, user_login)
);

create table list_rating
(
    rating_value real DEFAULT 0.0,
    id_list int NOT NULL,
    user_login varchar(30) NOT NULL,
    FOREIGN KEY (id_list) REFERENCES word_list (id_list),
    FOREIGN KEY (user_login) REFERENCES user_db (user_login),
    PRIMARY KEY (id_list, user_login)
);

create table word(
    word_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    word_name varchar(60) NOT NULL,
    word_translation varchar(60) NOT NULL,
    id_list INT NOT NULL,
    FOREIGN KEY(id_list) REFERENCES word_list(id_list)
);

create table word_usage(
    word_example_id INT PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    usage_example text,
    example_translation text,
    word_id INT NOT NULL,
    FOREIGN KEY(word_id) REFERENCES word(word_id)
);

create table word_learning(
    stage INT NOT NULL,
    date_gain_stage timestamp NOT NULL,
    user_login varchar(30) NOT NULL,
    word_id INT NOT NULL,
    FOREIGN KEY(word_id) REFERENCES word(word_id),
    FOREIGN KEY(user_login) REFERENCES user_db(user_login),
    PRIMARY KEY(word_id, user_login)
);


DROP FUNCTION IF EXISTS noexample();
CREATE FUNCTION noexample() RETURNS TRIGGER AS $updatenoexample$
BEGIN
    IF NEW.usage_example = '' THEN
        UPDATE word_usage SET usage_example = 'NoExample' WHERE word_example_id = NEW.word_example_id;
    END IF;
    IF NEW.example_translation = '' THEN
        UPDATE word_usage SET example_translation = 'NoExample'WHERE word_example_id = NEW.word_example_id;
    END IF;

    RETURN NEW;

    END;
$updatenoexample$ LANGUAGE plpgsql;

CREATE TRIGGER updatenoexample
AFTER INSERT ON word_usage
FOR EACH ROW
EXECUTE PROCEDURE noexample();


-- insert into user_db (user_login, user_password, full_name)
-- values ('Grape', '1234', ''),
--        ('Apple', '1235', 'Me');
--
-- insert into word_list (name_list)
-- values ('Phonk'),
--        ('English');
--
-- insert into users_list (id_list, user_login)
-- values (1, 'Apple'),
--        (2, 'Grape');
--
-- insert into word (id_word, name_word, definition, usage_example, id_list)
-- values (1, 'Drink', 'Пить', 'I drink vodka on Mondays', 1),
--        (2, 'Distinguish', 'Различать', 'I don''t distinguish between good and bas people', 1),
--        (3, 'Drill', 'Дрель', 'I''ll fo fire up the biopsy drill', 2);
--
-- insert into word_learning(stage, date_gain_stage, user_login, list_id, id_word)
-- values (1, '2022-10-13', 'Grape', 1, 1),
--        (2, '2022-10-10', 'Grape', 2, 3),
--        (2, '2022-10-11', 'Apple', 2, 3);
--
-- --у юзера нет подборки, но может учить слово из этой подборки
--
-- select * from user_db;
-- select * from word_list;
-- select * from users_list;
-- select * from word;
-- select * from word_learning;
