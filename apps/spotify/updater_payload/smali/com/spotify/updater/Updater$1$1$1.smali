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
    .registers 7
    .param p1, "dialog"  # Landroid/content/DialogInterface;
    .param p2, "which"  # I

    new-instance v0, Landroid/content/Intent;

    iget-object v1, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;

    iget-object v1, v1, Lstoreautoupdater/Updater$1$1;->this$1:Lstoreautoupdater/Updater$1;

    iget-object v1, v1, Lstoreautoupdater/Updater$1;->val$context:Landroid/content/Context;

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

    iget-object v1, p0, Lstoreautoupdater/Updater$1$1$1;->this$2:Lstoreautoupdater/Updater$1$1;

    iget-object v1, v1, Lstoreautoupdater/Updater$1$1;->this$1:Lstoreautoupdater/Updater$1;

    iget-object v1, v1, Lstoreautoupdater/Updater$1;->val$context:Landroid/content/Context;

    invoke-virtual {v1, v0}, Landroid/content/Context;->startService(Landroid/content/Intent;)Landroid/content/ComponentName;

    return-void
.end method
