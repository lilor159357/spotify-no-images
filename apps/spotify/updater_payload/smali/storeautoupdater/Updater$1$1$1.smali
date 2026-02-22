# classes.dex

.class Lstoreautoupdater/Updater$1$1$1;
.super Ljava/lang/Object;

# interfaces
.implements Landroid/content/DialogInterface$OnClickListener;

# instance fields
.field final synthetic this$2:Lstoreautoupdater/Updater$1$1;

# direct methods
.method constructor <init>(Lstoreautoupdater/Updater$1$1;)V
    .registers 2

    iput-object p1, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

# virtual methods
.method public onClick(Landroid/content/DialogInterface;I)V
    .registers 8
    .param p1, "dialog"  # Landroid/content/DialogInterface;
    .param p2, "which"  # I

    # משיכת ה-Context (Activity) מתוך המחלקות העוטפות
    iget-object v1, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;
    iget-object v1, v1, Lstoreautoupdater/Updater$1$1;->this$1:Lstoreautoupdater/Updater$1;
    iget-object v1, v1, Lstoreautoupdater/Updater$1;->val$context:Landroid/content/Context;

    # בדיקה אם מדובר באנדרואיד 13 (API 33) ומעלה
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I
    const/16 v2, 0x21
    if-lt v0, v2, :cond_start_service

    # בדיקה האם כבר ניתנה הרשאת התראות
    const-string v2, "android.permission.POST_NOTIFICATIONS"
    invoke-virtual {v1, v2}, Landroid/content/Context;->checkSelfPermission(Ljava/lang/String;)I
    move-result v0

    # אם 0 (מורשה) מדלג ישר להפעלת ה-Service
    if-nez v0, :cond_request_permission
    goto :cond_start_service

    :cond_request_permission
    # בקשת ההרשאה מתוך ה-Activity
    move-object v0, v1
    check-cast v0, Landroid/app/Activity;
    const/4 v3, 0x1
    new-array v3, v3, [Ljava/lang/String;
    const/4 v4, 0x0
    aput-object v2, v3, v4
    const/16 v2, 0x65
    invoke-virtual {v0, v3, v2}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V

    :cond_start_service
    # הכנה והפעלה של ה-DownloadService (פועל ברקע)
    new-instance v0, Landroid/content/Intent;
    const-class v2, Lstoreautoupdater/DownloadService;
    invoke-direct {v0, v1, v2}, Landroid/content/Intent;-><init>(Landroid/content/Context;Ljava/lang/Class;)V

    const-string v2, "url"
    iget-object v3, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;
    iget-object v3, v3, Lstoreautoupdater/Updater$1$1;->val$downloadUrl:Ljava/lang/String;
    invoke-virtual {v0, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    const-string v2, "version"
    iget-object v3, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;
    iget-object v3, v3, Lstoreautoupdater/Updater$1$1;->val$newVersion:Ljava/lang/String;
    invoke-virtual {v0, v2, v3}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;

    invoke-virtual {v1, v0}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;

    return-void
.end method
