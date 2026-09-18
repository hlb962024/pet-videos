import os
import requests
from urllib.parse import quote
from time import sleep

# ==================== 宠物列表 ====================
PETS = {
    "山海灵宠": ["毕方", "凤凰", "蛊雕", "精卫", "九尾狐", "天狗"],
    "国风神兽": ["白虎", "独角兽", "多肉精灵", "貔貅", "青龙", "狻猊", "朱雀"],
    "生肖萌宝": ["辰龙", "丑牛", "亥猪", "卯兔", "申猴", "巳蛇", "未羊", "午马", "戌狗", "寅虎", "酉鸡", "子鼠"],
    "萌犬天团": ["比熊", "边牧", "柴犬", "哈士奇", "小黑柴", "金毛", "柯基犬", "马尔济斯", "萨摩耶", "西高地", "西施犬", "雪纳瑞"],
    "软萌喵星": ["波斯猫", "布偶猫", "德文卷毛猫", "虎斑猫", "加菲猫", "金渐层", "橘猫", "缅因猫", "暹罗猫", "银渐层猫"],
    "绿野部落": [
        "安哥拉兔", "北极狼", "仓鼠", "垂耳兔", "小刺猬", "大象", "大熊猫", "小狐狸", "小浣熊", "小考拉",
        "柯尔鸭", "恐龙", "蓝孔雀", "龙猫", "芦丁鸡", "梅花鹿", "美洲豹", "蜜袋鼬", "绵羊", "狮子",
        "小松鼠", "小土拨鼠", "蜥蜴", "香猪", "小熊猫", "玄凤鹦鹉", "雪貂", "驯鹿", "羊驼", "长颈鹿"
    ],
    "水中伙伴": ["巴西龟", "小海豹", "海马", "小海兔", "寄居蟹", "六角恐龙", "企鹅", "水獭"],
}

# ==================== 配置 ====================
BASE_URL = "https://otf-pub-cdn.ourteacher.cc/uploads/all-pets"
ROOT_DIR = "animal-pet-images"   # 根文件夹
MAX_LEVEL = 8                    # 每个宠物 8 个等级
RETRY_TIMES = 3
TIMEOUT = 30
RETRY_DELAY = 2

# ==================== 下载函数 ====================
def download_pet_images(series, name, pet_idx, total_pets):
    """
    下载单个宠物的 8 个等级图片，保存到 animal-pet-images/系列名/宠物名/ 下
    返回 (成功数量, 失败列表)
    """
    # 创建宠物专属文件夹
    pet_dir = os.path.join(ROOT_DIR, series, name)
    os.makedirs(pet_dir, exist_ok=True)

    success = 0
    failed_levels = []

    for level in range(1, MAX_LEVEL + 1):
        local_path = os.path.join(pet_dir, f"{name}{level}.png")

        # 已存在则跳过
        if os.path.exists(local_path):
            print(f"   ⏭️  Lv.{level} 已存在，跳过")
            success += 1
            continue

        encoded_name = quote(name, safe='')
        url = f"{BASE_URL}/{encoded_name}{level}.png"

        downloaded = False
        for attempt in range(1, RETRY_TIMES + 1):
            try:
                print(f"   ⬇️  Lv.{level} (尝试 {attempt}/{RETRY_TIMES}) ...", end=" ")
                resp = requests.get(url, stream=True, timeout=TIMEOUT)

                if resp.status_code == 200:
                    with open(local_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print("✅")
                    success += 1
                    downloaded = True
                    break

                elif resp.status_code == 404:
                    print(f"⚠️ 404 不存在")
                    break  # 404 不重试

                else:
                    print(f"⚠️ HTTP {resp.status_code}")

            except requests.exceptions.Timeout:
                print(f"❌ 超时")
            except requests.exceptions.ConnectionError as e:
                print(f"❌ 连接错误: {e}")
            except Exception as e:
                print(f"❌ 异常: {type(e).__name__} - {e}")

            if attempt < RETRY_TIMES:
                sleep(RETRY_DELAY)

        if not downloaded:
            failed_levels.append(level)
            print(f"   ❌ Lv.{level} 最终失败")

    return success, failed_levels


# ==================== 主流程 ====================
def main():
    os.makedirs(ROOT_DIR, exist_ok=True)

    # 构造任务列表
    tasks = []
    for series, names in PETS.items():
        for name in names:
            tasks.append((series, name))

    total_pets = len(tasks)
    print(f"🐾 共 {total_pets} 个宠物，每个 {MAX_LEVEL} 个等级，预计 {total_pets * MAX_LEVEL} 张图片\n")

    total_success = 0
    total_failed = []
    pet_stats = []

    for idx, (series, name) in enumerate(tasks, 1):
        pct = idx / total_pets * 100
        print(f"\n{'='*55}")
        print(f"📦 [{idx}/{total_pets}] ({pct:.1f}%) {series} / {name}")
        print(f"{'='*55}")

        ok, failed = download_pet_images(series, name, idx, total_pets)
        total_success += ok
        if failed:
            for lv in failed:
                total_failed.append(f"{series}/{name} Lv.{lv}")

        pet_stats.append((series, name, ok, len(failed)))
        print(f"   📊 本宠物: {ok}/{MAX_LEVEL} 成功")

    # ==================== 汇总 ====================
    print(f"\n{'='*55}")
    print(f"🎉 全部完成！")
    print(f"{'='*55}")
    print(f"✅ 成功: {total_success}/{total_pets * MAX_LEVEL}")
    print(f"❌ 失败: {len(total_failed)} 张")

    if total_failed:
        print(f"\n失败明细：")
        for f in total_failed:
            print(f"  - {f}")

    # 按系列汇总
    print(f"\n📁 各系列统计：")
    series_stats = {}
    for series, name, ok, fail in pet_stats:
        if series not in series_stats:
            series_stats[series] = [0, 0]
        series_stats[series][0] += ok
        series_stats[series][1] += fail

    for series, (ok, fail) in series_stats.items():
        print(f"   {series}: 成功 {ok}, 失败 {fail}")


if __name__ == "__main__":
    main()