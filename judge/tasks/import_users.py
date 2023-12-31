import csv
from tempfile import mktemp

from django.conf import settings
from django.contrib.auth.models import User

from judge.models import Profile, Language, Organization, Contest


fields = ["username", "password", "name", "class", "email", "organizations", "contests"]
descriptions = [
    "my_username(edit old one if exist)",
    "123456 (must have)",
    "Le Van A (can be empty)",
    "SEEE (can be empty)",
    "email@email.com (can be empty)",
    "org1&org2&org3&... (can be empty - org slug in URL)",
    "cts&cts&cts&... (id contest)",
]


def csv_to_dict(csv_file):
    rows = csv.reader(csv_file.read().decode().split("\n"))
    header = next(rows)
    header = [i.lower() for i in header]

    if "username" not in header:
        return []

    res = []

    for row in rows:
        if len(row) != len(header):
            continue
        cur_dict = {i: "" for i in fields}
        for i in range(len(header)):
            if header[i] not in fields:
                continue
            cur_dict[header[i]] = row[i]
        if cur_dict["username"]:
            res.append(cur_dict)
    return res


# return result log
def import_users(users):
    log = ""
    for i, row in enumerate(users):
        cur_log = str(i + 1) + ". "

        username = row["username"]
        cur_log += username + ": "

        pwd = row["password"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_active": True,
            },
        )

        profile, _ = Profile.objects.get_or_create(
            user=user,
            defaults={
                "language": Language.get_python3(),
                "timezone": settings.DEFAULT_USER_TIME_ZONE,
            },
        )

        if created:
            cur_log += "Create new - "
        else:
            cur_log += "Edit - "

        if pwd:
            user.set_password(pwd)
        elif created:
            user.set_password(username)
            cur_log += "Missing password, set password = "+ username +" - "

        if "name" in row.keys() and row["name"]:
            user.first_name = row["name"]

        if "class" in row.keys() and row["class"]:
            user.last_name = row["class"]

        if row["organizations"]:
            orgs = row["organizations"].split("&")
            added_orgs = []
            for o in orgs:
                try:
                    org = Organization.objects.get(slug=o)
                    profile.organizations.add(org)
                    added_orgs.append(org.name)
                except Organization.DoesNotExist:
                    continue
            if added_orgs:
                cur_log += "Added to " + ", ".join(added_orgs) + " - "

        if row["email"]:
            user.email = row["email"]

        if row["contests"]:
            contests = row["contests"].split("&")
            added_contests = []
            for c in contests:
                try:
                    contest = Contest.objects.get(key=c)
                    contest.private_contestants.add(profile)
                    private_contestants = contest.private_contestants.all()
                    contest.private_contestants.set(private_contestants)
                    contest.save()
                    added_contests.append(contest.name)
                except Contest.DoesNotExist:
                    continue

            if added_contests:
                cur_log += "Added to " + ", ".join(added_contests) + " - "

        user.save()
        profile.save()
        cur_log += "Saved\n"
        log += cur_log
    log += "FINISH"

    return log
