.class final Lcom/spotify/updater/Updater$1;
.super Ljava/lang/Object;

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field final synthetic val$context:Landroid/content/Context;


# direct methods
.method constructor <init>(Landroid/content/Context;)V
    .registers 2
    .param p1, "context"  # Landroid/content/Context;

    iput-object p1, p0, Lcom/spotify/updater/Updater$1;->val$context:Landroid/content/Context;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .registers 12

    :try_start_0
    # 1. קבלת הגרסה הנוכחית של האפליקציה (v0)
    iget-object v8, p0, Lcom/spotify/updater/Updater$1;->val$context:Landroid/content/Context;

    invoke-virtual {v8}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    move-result-object v3

    iget-object v8, p0, Lcom/spotify/updater/Updater$1;->val$context:Landroid/content/Context;

    invoke-virtual {v8}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object v8

    const/4 v9, 0x0

    invoke-virtual {v3, v8, v9}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;

    move-result-object v1

    iget-object v0, v1, Landroid/content/pm/PackageInfo;->versionName:Ljava/lang/String;

    # 2. התחברות לקובץ הגרסה הגולמי (Raw Text)
    new-instance v7, Ljava/net/URL;

    const-string v8, "https://raw.githubusercontent.com/lilor159357/spotify-no-images/refs/heads/main/apps/spotify/version.txt"

    invoke-direct {v7, v8}, Ljava/net/URL;-><init>(Ljava/lang/String;)V

    invoke-virtual {v7}, Ljava/net/URL;->openConnection()Ljava/net/URLConnection;

    move-result-object v9

    check-cast v9, Ljava/net/HttpURLConnection;

    # הגדרת User-Agent וביטול מטמון (Cache) כדי לקבל תמיד את הגרסה העדכנית
    const-string v10, "User-Agent"
    const-string v8, "SpotifyUpdater"
    invoke-virtual {v9, v10, v8}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V
    const-string v10, "Cache-Control"
    const-string v8, "no-cache"
    invoke-virtual {v9, v10, v8}, Ljava/net/HttpURLConnection;->setRequestProperty(Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v9}, Ljava/net/HttpURLConnection;->getInputStream()Ljava/io/InputStream;

    move-result-object v2

    # 3. קריאת תוכן הקובץ (הגרסה החדשה)
    new-instance v5, Ljava/util/Scanner;

    invoke-direct {v5, v2}, Ljava/util/Scanner;-><init>(Ljava/io/InputStream;)V

    const-string v8, "\\A"

    invoke-virtual {v5, v8}, Ljava/util/Scanner;->useDelimiter(Ljava/lang/String;)Ljava/util/Scanner;

    move-result-object v8

    invoke-virtual {v8}, Ljava/util/Scanner;->next()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v5}, Ljava/util/Scanner;->close()V

    # 4. ניקוי רווחים ותווים מיותרים (v8 = הגרסה החדשה)
    invoke-virtual {v4}, Ljava/lang/String;->trim()Ljava/lang/String;
    move-result-object v8

    # 5. השוואה: האם הגרסה הנוכחית (v0) שונה מהחדשה (v8)?
    invoke-virtual {v0, v8}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v9

    if-nez v9, :cond_exit

    # 6. בניית קישור ההורדה באופן דינמי (v9 = downloadUrl)
    # תבנית: .../download/spotify-v{VER}/spotify-patched-{VER}.apk
    new-instance v9, Ljava/lang/StringBuilder;
    invoke-direct {v9}, Ljava/lang/StringBuilder;-><init>()V
    const-string v6, "https://github.com/lilor159357/spotify-no-images/releases/download/spotify-v"
    invoke-virtual {v9, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, "/spotify-patched-"
    invoke-virtual {v9, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v6, ".apk"
    invoke-virtual {v9, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v9}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v9

    # 7. הפעלת הדיאלוג (UI Thread)
    new-instance v10, Landroid/os/Handler;
    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v10, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    # העברת הגרסה החדשה (v8) וקישור ההורדה (v9) לדיאלוג
    new-instance v1, Lcom/spotify/updater/Updater$1$1;
    invoke-direct {v1, p0, v0, v8, v9}, Lcom/spotify/updater/Updater$1$1;-><init>(Lcom/spotify/updater/Updater$1;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V

    invoke-virtual {v10, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    :cond_exit
    :goto_exit
    return-void

    :catch_error
    move-exception v8
    const-string v9, "SpotifyUpdater"
    invoke-virtual {v8}, Ljava/lang/Exception;->toString()Ljava/lang/String;
    move-result-object v10
    invoke-static {v9, v10}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
    goto :goto_exit
.end method
