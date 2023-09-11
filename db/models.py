from typing import Callable, Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint


class Genre(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:
        return self.name


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    actors = models.ManyToManyField(to=Actor)
    genres = models.ManyToManyField(to=Genre)

    def __str__(self) -> str:
        return self.title


class CinemaHall(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self) -> str:
        return self.name


class MovieSession(models.Model):
    show_time = models.DateTimeField()
    cinema_hall = models.ForeignKey(to=CinemaHall, on_delete=models.CASCADE)
    movie = models.ForeignKey(to=Movie, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.movie.title} {str(self.show_time)}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"{self.created_at}"

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    movie_session = models.ForeignKey(
        MovieSession, related_name="tickets", on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order, related_name="tickets", on_delete=models.CASCADE
    )
    row = models.IntegerField()
    seat = models.IntegerField()

    def __str__(self) -> str:
        return (
            f"{str(self.movie_session)} (row: {self.row}, seat: {self.seat})"
        )

    def clean(self) -> None:
        cinema_hall = self.movie_session.cinema_hall
        if not 1 <= self.row <= cinema_hall.rows:
            raise ValidationError(
                {
                    "row": [
                        "row number must be in available range: "
                        "(1, rows): (1, {})".format(cinema_hall.rows)
                    ]
                },
                code="seat_out_of_range",
            )

        if not 1 <= self.seat <= cinema_hall.seats_in_row:
            raise ValidationError(
                {
                    "seat": [
                        "seat number must be in available range: "
                        "(1, seats_in_row): (1, {})".format(
                            cinema_hall.seats_in_row
                        )
                    ]
                },
                code="seat_out_of_range",
            )

    def save(
        self,
        force_insert: bool = False,
        force_update: bool = False,
        using: Any = None,
        update_fields: Any = None,
    ) -> Callable:
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["row", "seat", "movie_session"],
                name="unique_ticket_constraint_name",
            )
        ]


class User(AbstractUser):  # noqa: F811
    pass
