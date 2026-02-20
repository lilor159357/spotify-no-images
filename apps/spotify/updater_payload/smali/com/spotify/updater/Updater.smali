# classes.dex

.class public Lcom/spotify/updater/Updater;
.super Ljava/lang/Object;
.source "Updater.java"


# static fields
.field private static final GITHUB_API_URL:Ljava/lang/String; = "https://api.github.com/repos/lilor159357/spotify-no-images/releases/latest"


# direct methods
.method public constructor <init>()V
    .registers 1

    .prologue
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static check(Landroid/content/Context;)V
    .registers 3
    .param p0, "context"  # Landroid/content/Context;

    .prologue
    new-instance v0, Ljava/lang/Thread;

    new-instance v1, Lcom/spotify/updater/Updater$1;

    invoke-direct {v1, p0}, Lcom/spotify/updater/Updater$1;-><init>(Landroid/content/Context;)V

    invoke-direct {v0, v1}, Ljava/lang/Thread;-><init>(Ljava/lang/Runnable;)V

    invoke-virtual {v0}, Ljava/lang/Thread;->start()V

    return-void
.end method
